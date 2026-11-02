"""Bounded PE import-table observation. No image loading or execution."""
import struct
import re

from ..v1.records import Refusal, require, exact_int, windows_path

MAX_NAMES = 4096
MAX_SECTIONS = 96


def host_basename(value):
    """Closed API metadata basename grammar; this grants no platform trust."""
    require(type(value) is str and re.fullmatch(r'[a-z0-9_.-]+\.(dll|sys|drv)', value) is not None,
            'API host basename')
    windows_path(value)
    require('/' not in value and '..' not in value, 'API host basename')
    return value


def api_set_namespace(raw):
    """Derive the exact v6 namespace from bounded retained OS metadata bytes."""
    require(type(raw) is bytes and 64<=len(raw)<=2*1024**2,'API image bytes')
    def span(offset,length):
        require(type(offset) is int and type(length) is int and offset>=0 and
                length>=0 and offset+length<=len(raw),'API image range')
        return raw[offset:offset+length]
    require(span(0,2)==b'MZ','API DOS signature')
    offset=struct.unpack('<I',span(60,4))[0]
    require(64<=offset<=1024**2 and span(offset,4)==b'PE\0\0','API PE header')
    count=struct.unpack('<H',span(offset+6,2))[0]
    optional=struct.unpack('<H',span(offset+20,2))[0]
    require(1<=count<=96 and 96<=optional<=4096,'API PE table bounds')
    table=span(offset+24+optional,count*40)
    sections=[]
    for i in range(count):
        row=table[i*40:(i+1)*40]
        if row[:8].rstrip(b'\0')==b'.apiset':
            size,start=struct.unpack_from('<II',row,16)
            sections.append(span(start,size))
    require(len(sections)==1,'unique API namespace section')
    data=sections[0]
    require(len(data)>=28,'API namespace header')
    version,size,flags,count,entries,hashes,factor=struct.unpack_from('<7I',data)
    require(version==6 and 28<=size<=len(data) and count<=4096,'API namespace version/size/count')
    data=data[:size]
    def area(offset,length):
        require(offset>=0 and length>=0 and offset+length<=len(data),'API namespace range')
        return data[offset:offset+length]
    def string(offset,length):
        require(length%2==0 and length<=1024,'API string length')
        return area(offset,length).decode('utf-16-le').lower()
    area(entries,count*24)
    result={}
    for i in range(count):
        _,name_offset,name_length,hashed_length,values,n=struct.unpack('<6I',area(entries+i*24,24))
        require(hashed_length<=name_length and n<=256,'API entry bounds')
        name=string(name_offset,name_length)
        require(re.fullmatch(r'(api|ext)-[a-z0-9-]+',name) is not None,'API name')
        key=name+'.dll'
        require(key not in result,'duplicate API name')
        hosts=set()
        area(values,n*20)
        for j in range(n):
            _,alias_offset,alias_length,host_offset,host_length=struct.unpack('<5I',area(values+j*20,20))
            string(alias_offset,alias_length)
            host=string(host_offset,host_length)
            if host:hosts.add(host_basename(host))
        result[key]=sorted(hosts)
    return dict(sorted(result.items()))


def imports(read_at, size):
    """Read only explicit bounded ranges of an already retained image.

    read_at(offset, count) must supply exact original-handle bytes under guards.
    This records import and delay-import names; it does not certify ABI or search.
    """
    require(callable(read_at), "retained range callback")
    exact_int(size, 64, 2 * 1024**3)

    def read(offset, count):
        exact_int(offset, 0, size)
        exact_int(count, 0, 65536)
        require(offset + count <= size, "PE range outside retained file")
        raw = read_at(offset, count)
        require(type(raw) is bytes and len(raw) == count, "exact PE range bytes")
        return raw

    dos = read(0, 64)
    require(dos[:2] == b'MZ', "DOS signature")
    offset = struct.unpack_from('<I', dos, 60)[0]
    require(64 <= offset <= 1024**2, "PE header offset bound")
    header = read(offset, 24)
    require(header[:4] == b'PE\0\0', "PE signature")
    machine, count = struct.unpack_from('<HH', header, 4)
    require(machine in (0x14c, 0x8664, 0xaa64), "declared PE architecture")
    require(1 <= count <= MAX_SECTIONS, "section count")
    optional_size = struct.unpack_from('<H', header, 20)[0]
    require(96 <= optional_size <= 4096, "optional header bound")
    optional = read(offset + 24, optional_size)
    magic = struct.unpack_from('<H', optional)[0]
    require(magic in (0x10b, 0x20b), "PE optional magic")
    directory_offset = 96 if magic == 0x10b else 112
    require(optional_size >= directory_offset, "truncated optional header")
    directories = struct.unpack_from('<I', optional, directory_offset - 4)[0]
    require(directories <= 16 and optional_size >= directory_offset + 8 * directories,
            "data directory count/bounds")
    header_size = struct.unpack_from('<I', optional, 60)[0]
    require(header_size <= size, "image header size")
    section_bytes = read(offset + 24 + optional_size, count * 40)
    sections = []
    for index in range(count):
        virtual_size, virtual, raw_size, raw = struct.unpack_from('<IIII', section_bytes, index * 40 + 8)
        require(raw + raw_size <= size, "section raw range")
        sections.append((virtual, max(virtual_size, raw_size), raw, raw_size))

    def physical(rva, length):
        candidates = []
        if rva < header_size and rva + length <= header_size:
            candidates.append(rva)
        for virtual, span, raw, raw_size in sections:
            if virtual <= rva and rva + length <= virtual + span:
                require(rva - virtual + length <= raw_size, "unbacked PE virtual range")
                candidates.append(raw + rva - virtual)
        require(len(candidates) == 1, "missing/ambiguous RVA")
        return candidates[0]

    def name(rva):
        spans = []
        if rva < header_size: spans.append(header_size-rva)
        for virtual, span, raw, raw_size in sections:
            if virtual <= rva < virtual+span:
                require(rva-virtual < raw_size, 'unbacked import name')
                spans.append(raw_size-(rva-virtual))
        require(len(spans)==1, 'import name mapping')
        length=min(260,spans[0])
        raw=read(physical(rva,length),length)
        require(b'\0' in raw,'DLL import name bound')
        chars=raw.split(b'\0',1)[0]
        require(chars and all(32<c<127 and chr(c) not in '/\\:' for c in chars),'DLL basename spelling')
        text=chars.decode('ascii').lower()
        require(text.endswith(('.dll','.exe','.pyd','.drv')),'import suffix')
        return text

    result, descriptors = {}, []
    for label, directory, stride, name_offset in (('imports', 1, 20, 12), ('delay_imports', 13, 32, 4)):
        names = []
        if directory < directories:
            rva, length = struct.unpack_from('<II', optional, directory_offset + directory * 8)
            require((rva == 0) == (length == 0), "partial import directory")
            if rva:
                require(stride <= length <= (MAX_NAMES + 1) * stride, "import directory bound")
                terminated = False
                for i in range(min(length // stride, MAX_NAMES + 1)):
                    row = read(physical(rva + i * stride, stride), stride)
                    if not any(row):
                        terminated = True
                        break
                    require(i < MAX_NAMES, "import count limit")
                    if label == 'delay_imports':
                        require(struct.unpack_from('<I', row)[0] == 1, "delay descriptor must use RVAs")
                    name_rva = struct.unpack_from('<I', row, name_offset)[0]
                    basename = name(name_rva)
                    names.append(basename)
                    descriptors.append({'kind': label, 'index': i,
                        'descriptor_rva': rva + i * stride, 'name_rva': name_rva,
                        'name': basename, 'descriptor_bytes_hex': row.hex()})
                require(terminated, "unterminated import table")
        # Names remain in descriptor-table order, including every occurrence.
        result[label] = names
    return {"schema": "cho51_p2_pe_imports_v2", "machine": machine,
            "optional_magic": magic, **result, "descriptors": descriptors,
            "image_loaded": False, "abi_qualified": False}


def resolve(observations, paths, platform_names, api_sets=None):
    """Proposed physical candidate closure, not actual Windows search selection.

    All non-platform imports need at least one selected physical candidate.
    Ambiguous candidates remain explicit and must receive per-importer loader
    search review before L; no arbitrary first-match or basename attestation.
    """
    require(api_sets is None or type(api_sets) is dict,'exact supplied API namespace')
    api_sets={} if api_sets is None else api_sets
    by_name = {}
    for path in paths:
        by_name.setdefault(path.rsplit('/', 1)[-1].lower(), []).append(path)
    edges, missing = [], []
    for path, observation in sorted(observations.items()):
        by_occurrence = {}
        for kind in ('imports', 'delay_imports'):
            for index, basename in enumerate(observation[kind]):
                by_occurrence.setdefault(basename, []).append({'kind': kind, 'index': index})
        for name, occurrences in sorted(by_occurrence.items()):
            # One physical resolution question per basename, with explicit
            # multiplicity/table position; repeated entries are never erased.
            if name in platform_names:
                edges.append({'importer': path, 'name': name, 'kind': 'declared_platform_trust', 'candidates': []})
            elif name in api_sets and api_sets[name] and all(host in platform_names for host in api_sets[name]):
                edges.append({'importer':path,'name':name,'kind':'reviewed_api_set_namespace',
                              'candidates':[],'platform_hosts':list(api_sets[name])})
            else:
                candidates = sorted(by_name.get(name, []))
                if not candidates:
                    missing.append({'importer': path, 'name': name})
                edges.append({'importer': path, 'name': name, 'kind': 'selected_physical_candidates',
                              'candidates': candidates})
            edges[-1]['occurrences'] = occurrences
            edges[-1]['occurrence_count'] = len(occurrences)
    return {'schema': 'cho51_p2_pe_resolution_v2', 'edges': edges, 'missing': missing,
            'complete_physical_candidates': not missing, 'native_search_qualified': False,
            'launch_authorized': False, 'scientific_admission': False}




