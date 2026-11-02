"""Pure synthetic-byte PE controls; no native image is executed."""
import struct
import unittest

from . import pe
from ..v1.records import Refusal


def fixture():
    data = bytearray(1024)
    data[:2] = b'MZ'
    struct.pack_into('<I', data, 60, 64)
    data[64:68] = b'PE\0\0'
    struct.pack_into('<HH', data, 68, 0x8664, 1)
    struct.pack_into('<H', data, 84, 240)
    struct.pack_into('<H', data, 88, 0x20b)
    struct.pack_into('<I', data, 148, 512)
    struct.pack_into('<I', data, 196, 16)
    struct.pack_into('<II', data, 208, 0x1000, 40)
    struct.pack_into('<IIII', data, 336, 512, 0x1000, 512, 512)
    struct.pack_into('<I', data, 524, 0x1080)
    data[640:653] = b'kernel32.dll\0'
    return data


class PEControls(unittest.TestCase):
    def namespace_fixture(self):
        data=fixture()
        data[328:336]=b'.apiset\0'
        struct.pack_into('<7I',data,512,6,512,0,1,28,0,0)
        name='api-ms-win-test-l1-1-0'.encode('utf-16-le')
        host='kernel32.dll'.encode('utf-16-le')
        struct.pack_into('<6I',data,540,0,80,len(name),len(name),52,1)
        struct.pack_into('<5I',data,564,0,0,0,128,len(host))
        data[592:592+len(name)]=name;data[640:640+len(host)]=host
        return data

    def test_api_namespace_derives_exact_names_and_hosts(self):
        self.assertEqual(pe.api_set_namespace(bytes(self.namespace_fixture())),
            {'api-ms-win-test-l1-1-0.dll':['kernel32.dll']})

    def test_api_namespace_version_ranges_and_host_refused(self):
        for offset,value in ((512,7),(516,1025),(528,1000),(564+12,1000)):
            data=self.namespace_fixture();struct.pack_into('<I',data,offset,value)
            with self.subTest(offset=offset),self.assertRaises(Refusal):pe.api_set_namespace(bytes(data))

    def parse(self, data):
        return pe.imports(lambda offset, size: bytes(data[offset:offset+size]), len(data))

    def test_real_layout_synthetic_import(self):
        result = self.parse(fixture())
        self.assertEqual(result['imports'], ['kernel32.dll'])
        self.assertFalse(result['image_loaded'])

    def test_signature_refusal(self):
        data = fixture(); data[0] = 0
        with self.assertRaises(Refusal): self.parse(data)

    def test_header_offset_bound(self):
        data = fixture(); struct.pack_into('<I', data, 60, 2**30)
        with self.assertRaises(Refusal): self.parse(data)

    def test_section_bounds(self):
        data = fixture(); struct.pack_into('<I', data, 348, 1024)
        with self.assertRaises(Refusal): self.parse(data)

    def test_short_range_refused(self):
        with self.assertRaises(Refusal): pe.imports(lambda offset, size: b'', 1024)

    def test_boolean_size_refused(self):
        with self.assertRaises(Refusal): pe.imports(lambda offset, size: b'', True)

    def test_unbacked_name_rva(self):
        data = fixture(); struct.pack_into('<I', data, 524, 0x2000)
        with self.assertRaises(Refusal): self.parse(data)

    def test_path_import_refused(self):
        data = fixture(); data[640:653] = b'../evil.dll\0\0'
        with self.assertRaises(Refusal): self.parse(data)

    def test_unterminated_directory(self):
        data = fixture(); struct.pack_into('<II', data, 208, 0x1000, 20)
        with self.assertRaises(Refusal): self.parse(data)

    def test_delay_rva_descriptor(self):
        data = fixture(); struct.pack_into('<II', data, 304, 0x1040, 64)
        struct.pack_into('<II', data, 576, 1, 0x1080)
        self.assertEqual(self.parse(data)['delay_imports'], ['kernel32.dll'])

    def test_delay_virtual_address_refused(self):
        data = fixture(); struct.pack_into('<II', data, 304, 0x1040, 64)
        struct.pack_into('<II', data, 576, 2, 0x1080)
        with self.assertRaises(Refusal): self.parse(data)

    def test_physical_candidates_not_search_qualification(self):
        observation = {'imports': ['x.dll'], 'delay_imports': []}
        value = pe.resolve({'D:/a.pyd': observation}, ['D:/one/x.dll','D:/two/x.dll'], [])
        self.assertTrue(value['complete_physical_candidates'])
        self.assertEqual(len(value['edges'][0]['candidates']), 2)
        self.assertFalse(value['native_search_qualified'])

    def test_missing_import_refuses_completion(self):
        value = pe.resolve({'D:/a.pyd': {'imports':['x.dll'], 'delay_imports':[]}}, [], [])
        self.assertFalse(value['complete_physical_candidates'])

    def test_explicit_platform_and_api_set(self):
        value = pe.resolve({'D:/a.pyd': {'imports':['kernel32.dll','api-ms-win-core-x.dll'], 'delay_imports':[]}}, [], ['kernel32.dll'], {'api-ms-win-core-x.dll':['kernel32.dll']})
        self.assertTrue(value['complete_physical_candidates'])
        self.assertFalse(value['launch_authorized'])

    def test_unknown_api_prefix_and_missing_host_refused(self):
        observation={'D:/a.pyd':{'imports':['api-ms-win-made-up.dll'],'delay_imports':[]}}
        self.assertFalse(pe.resolve(observation,[],[])['complete_physical_candidates'])
        self.assertFalse(pe.resolve(observation,[],[],{'api-ms-win-made-up.dll':['absent.dll']})['complete_physical_candidates'])


