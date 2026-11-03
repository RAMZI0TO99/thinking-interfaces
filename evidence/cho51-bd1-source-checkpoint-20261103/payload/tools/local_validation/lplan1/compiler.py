"""Finite source-pinned AST graph compiler for separately admitted preparation.

Reads retained Python text; never imports/executes inspected modules. Unknown
branch, dynamic import/effect or ambiguous origin is a recorded refusal. A
partial graph is evidence for review, never an import allowlist or L grant.
"""
import ast
import hashlib
from ..l1.protocol import need,closed,integer,string,encode

SCHEMA='cho51_l_plan_compiler_spec_v1'
DECISION_KINDS=('import','from','dynamic-import','dynamic-code','native-load','resource','branch','call')
DYNAMIC_IMPORTS=('__import__','importlib.import_module','importlib.__import__')
DYNAMIC_CODE=('exec','eval','compile','runpy.run_module','runpy.run_path')
NATIVE_CALLS=('ctypes.CDLL','ctypes.WinDLL','ctypes.cdll.LoadLibrary','ctypes.windll.LoadLibrary',
              'torch.ops.load_library','os.add_dll_directory','LoadLibraryW','LoadLibraryExW')
RESOURCE_CALLS=('open','io.open','os.open','importlib.resources.files','pkgutil.get_data','pkg_resources.resource_filename')

def dotted(node):
    if isinstance(node,ast.Name):return node.id
    if isinstance(node,ast.Attribute):
        prefix=dotted(node.value)
        return prefix+'.'+node.attr if prefix else None
    return None

def normal_ref(descriptor,role):
    return {**{key:descriptor[key] for key in ('path','bytes','sha256')},'role':role}

def call_bindings(tree,maximum_nodes,maximum_depth):
    """Conservative whole-source binding census; no scope/alias inference.

    A possible shadow anywhere makes the root unresolved everywhere. Exact
    unaliased import roots and unshadowed builtins are the only recognized calls.
    This deliberately refuses callable parameters, rebindings and object aliases.
    """
    shadowed=set();imports={};stack=[(tree,0)];count=0
    while stack:
        node,depth=stack.pop();count+=1
        need(count<=maximum_nodes and depth<=maximum_depth,'binding AST complexity bound')
        if isinstance(node,ast.Name) and isinstance(node.ctx,(ast.Store,ast.Del)):shadowed.add(node.id)
        if isinstance(node,ast.Attribute) and isinstance(node.ctx,(ast.Store,ast.Del)):
            name=dotted(node)
            if name:shadowed.add(name.split('.')[0])
        if isinstance(node,ast.arg):shadowed.add(node.arg)
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):shadowed.add(node.name)
        if isinstance(node,(ast.ExceptHandler,ast.MatchAs,ast.MatchStar)) and node.name:shadowed.add(node.name)
        if isinstance(node,ast.Import):
            for alias in node.names:
                root=alias.name.split('.')[0];bound=alias.asname or root
                if alias.asname or '.' in alias.name:shadowed.add(bound)
                else:imports[root]=imports.get(root,0)+1
        if isinstance(node,ast.ImportFrom):
            for alias in node.names:shadowed.add(alias.asname or alias.name)
        for child in ast.iter_child_nodes(node):stack.append((child,depth+1))
    return shadowed,imports

def recognized_binding(name,shadowed,imports):
    if name is None:return False
    root=name.split('.')[0]
    if root in shadowed:return False
    if root in ('__import__','exec','eval','compile','open'):return imports.get(root,0)==0
    return '.' in name and imports.get(root,0)==1

def validate_spec(spec):
    closed(spec,'schema roots seeds builtin_modules frozen_modules decisions module_choices phase_groups native_policy resource_policy abi_policy guard_policy pytest_policy bindings limits')
    need(spec['schema']==SCHEMA,'plan compiler spec schema')
    need(type(spec['roots']) is list and bool(spec['roots']),'ordered exact module roots')
    for row in spec['roots']:
        closed(row,'path prefix role');string(row['path'],32768);string(row['prefix'],2048,empty=True)
        need(row['role'] in ('runtime','dependency','project'),'module root role')
    for key in ('seeds','builtin_modules','frozen_modules'):
        need(type(spec[key]) is list and len(set(spec[key]))==len(spec[key]),'finite unique '+key)
        for value in spec[key]:string(value,2048)
    closed(spec['limits'],'modules edges source_bytes ast_nodes depth')
    for key,cap in dict(modules=25000,edges=200000,source_bytes=4*1024**3,ast_nodes=2000000,depth=128).items():
        integer(spec['limits'][key],1,cap)
    seen=set()
    for row in spec['decisions']:
        closed(row,'module source_sha256 line column kind action targets rationale effect_ids')
        need(row['kind'] in DECISION_KINDS and row['action'] in ('include','exclude','mediate'),'explicit branch/effect decision')
        integer(row['line'],1,1000000);integer(row['column'],0,100000)
        key=(row['module'],row['source_sha256'],row['line'],row['column'],row['kind'])
        need(key not in seen,'duplicate source decision');seen.add(key)
        string(row['rationale'],8192);need(type(row['targets']) is list and type(row['effect_ids']) is list,'finite decision targets/effects')
    need(type(spec['module_choices']) is dict and type(spec['phase_groups']) is dict,'finite module choice/group maps')
    encode(spec)
    return spec

def compile_plan(spec,physical,read_retained,checkpoint):
    validate_spec(spec)
    need(type(physical) is dict and callable(read_retained) and callable(checkpoint),'retained supplied preparation inputs')
    decisions={(r['module'],r['source_sha256'],r['line'],r['column'],r['kind']):r for r in spec['decisions']}
    used=set();refusals=[];derivation=[];imports={};edges=[];queue=list(spec['seeds']);total_bytes=0
    limits=spec['limits'];functions=0;source_nodes=0
    def refuse(module,kind,message,line=None,column=None):
        row=dict(module=module,kind=kind,line=line,column=column,message=message)
        if row not in refusals:refusals.append(row)
    def decision(module,pin,node,kind,required=True):
        key=(module,pin,node.lineno,node.col_offset,kind)
        row=decisions.get(key)
        if row is None:
            if required:refuse(module,kind,'missing exact source-pinned branch/effect decision',node.lineno,node.col_offset)
            return None
        used.add(key);derivation.append(dict(module=module,source_sha256=pin,line=node.lineno,column=node.col_offset,
                    kind=kind,action=row['action'],targets=row['targets'],rationale=row['rationale'],effect_ids=row['effect_ids']))
        return row
    def origins(module):
        values=[]
        for root in spec['roots']:
            prefix=root['prefix']
            if prefix and module!=prefix and not module.startswith(prefix+'.'):continue
            relative=module[len(prefix):].lstrip('.').replace('.','/')
            base=root['path'].rstrip('/')+('/'+relative if relative else '')
            for path,kind,namespace in ((base+'.py','source',[]),(base+'/__init__.py','source',[base]),
                                       (base+'.pyd','extension',[])):
                if path in physical:values.append((path,kind,namespace))
            # Tagged extension suffixes are selected only from an explicitly
            # reviewed module choice; no filename-family first-match fallback.
        choice=spec['module_choices'].get(module)
        if choice is not None:
            closed(choice,'kind path namespace_paths')
            if choice['kind']=='namespace':
                need(choice['path'] is None and bool(choice['namespace_paths']),'exact namespace choice')
                return [(None,'namespace',choice['namespace_paths'])]
            need(choice['path'] in physical,'chosen module absent from P')
            need(choice['kind'] in ('source','extension'),'chosen module kind')
            return [(choice['path'],choice['kind'],choice['namespace_paths'])]
        return values
    def add_edge(module,target,node,kind):
        string(target,2048)
        # Parent packages are executable imports too, never implicit grants.
        parts=target.split('.')
        for i in range(1,len(parts)+1):
            name='.'.join(parts[:i])
            edge=dict(source=module,target=name,line=node.lineno,column=node.col_offset,kind=kind)
            if edge not in edges:edges.append(edge)
            if name not in imports and name not in queue:queue.append(name)
        need(len(edges)<=limits['edges'],'plan edge bound')
    while queue:
        need(checkpoint() is True,'plan construction checkpoint')
        module=queue.pop(0)
        if module in imports:continue
        need(len(imports)<limits['modules'],'plan module bound')
        group=spec['phase_groups'].get(module)
        if group is None:
            refuse(module,'phase','module lacks exact reviewed initialization group');continue
        closed(group,'phase group_id')
        if module in spec['builtin_modules'] or module in spec['frozen_modules']:
            imports[module]=dict(module=module,kind='builtin' if module in spec['builtin_modules'] else 'frozen',file_ref=None,
                                 namespace_paths=[],phase=group['phase'],initializer_group=group['group_id']);continue
        choices=origins(module)
        if len(choices)!=1:
            refuse(module,'origin','missing or ambiguous exact module origin');continue
        path,kind,namespace=choices[0]
        reference=None if path is None else normal_ref(physical[path],'source' if kind=='source' else 'native_image')
        imports[module]=dict(module=module,kind=kind,file_ref=reference,namespace_paths=namespace,
                             phase=group['phase'],initializer_group=group['group_id'])
        if kind!='source':continue
        raw=read_retained(physical[path]);need(type(raw) is bytes and len(raw)==physical[path]['bytes']
             and hashlib.sha256(raw).hexdigest()==physical[path]['sha256'],'original retained plan source')
        total_bytes+=len(raw);need(total_bytes<=limits['source_bytes'],'plan source byte cap')
        try:tree=ast.parse(raw,filename=path,mode='exec')
        except (SyntaxError,ValueError,RecursionError) as error:
            refuse(module,'syntax',type(error).__name__);continue
        shadowed,import_roots=call_bindings(tree,limits['ast_nodes'],limits['depth'])
        stack=[(tree,None,0)]
        while stack:
            node,parent,depth=stack.pop();source_nodes+=1
            need(source_nodes<=limits['ast_nodes'] and depth<=limits['depth'],'plan AST complexity bound')
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.Lambda,ast.ClassDef)):
                # Definition bodies can contain dormant effects; explicit
                # source-pinned decisions distinguish these from eager code.
                functions+=1
            if isinstance(node,(ast.Import,ast.ImportFrom)):
                is_from=isinstance(node,ast.ImportFrom)
                kind_name='from' if is_from else 'import'
                row=decision(module,reference['sha256'],node,kind_name)
                if row is not None and row['action']=='include':
                    if not is_from:
                        need(set(row['targets'])=={alias.name for alias in node.names},'import decision must match literal syntax')
                    else:
                        package=module if path.endswith('/__init__.py') else module.rpartition('.')[0]
                        parts=package.split('.') if package else []
                        if node.level:
                            need(node.level<=len(parts)+1,'relative import scope')
                            base='.'.join(parts[:len(parts)-node.level+1]+([node.module] if node.module else []))
                        else:base=node.module or ''
                        need(base and base in row['targets'] and set(row['targets'])<=({base}|{base+'.'+a.name for a in node.names if a.name!='*'}),'from decision literal base/member syntax')
                        need(not any(alias.name=='*' for alias in node.names),'star imports require unsupported-syntax refusal')
                    for target in row['targets']:add_edge(module,target,node,kind_name)
                elif row is not None and row['action']=='mediate':
                    refuse(module,kind_name,'imports cannot be replaced by effect mediators',node.lineno,node.col_offset)
            elif isinstance(node,ast.Call):
                name=dotted(node.func)
                call_kind=('dynamic-import' if name in DYNAMIC_IMPORTS else 'dynamic-code' if name in DYNAMIC_CODE
                           else 'native-load' if name in NATIVE_CALLS else 'resource' if name in RESOURCE_CALLS else 'call')
                if call_kind is not None:
                    row=decision(module,reference['sha256'],node,call_kind)
                    # A dotted spelling is not proof of the callable's identity:
                    # assignments, getattr, closures, parameters and containers
                    # can hide imports/code/native/resource effects. No generic
                    # active call is certified by an include/mediator decision.
                    # Only a reviewed dormant exclusion avoids this refusal.
                    if call_kind=='call' and row is not None and row['action']!='exclude':
                        refuse(module,'unresolved-call-target','active indirect/generic callable identity is unresolved',node.lineno,node.col_offset)
                    if call_kind!='call' and row is not None and row['action']!='exclude' and not recognized_binding(name,shadowed,import_roots):
                        refuse(module,'unresolved-call-target','recognized spelling has an unproven or shadowed root binding',node.lineno,node.col_offset)
                    if row is not None and row['action']=='include' and call_kind=='dynamic-import':
                        if len(node.args)!=1 or node.keywords or not isinstance(node.args[0],ast.Constant) or type(node.args[0].value) is not str or node.args[0].value.startswith('.') or row['targets']!=[node.args[0].value]:
                            refuse(module,'unresolved-import-target','dynamic import requires one exact absolute literal target',node.lineno,node.col_offset)
                        else:
                            for target in row['targets']:add_edge(module,target,node,call_kind)
                    elif row is not None and row['action']=='mediate' and not row['effect_ids']:
                        refuse(module,call_kind,'mediation requires exact effect IDs',node.lineno,node.col_offset)
                    elif row is not None and row['action']=='include' and call_kind not in ('dynamic-import','call'):
                        refuse(module,call_kind,'effect requires mediation or reviewed dormant exclusion',node.lineno,node.col_offset)
            elif isinstance(node,(ast.If,ast.Try,ast.TryStar,ast.Match,ast.With,ast.AsyncWith)):
                decision(module,reference['sha256'],node,'branch')
            for child in reversed(list(ast.iter_child_nodes(node))):stack.append((child,node,depth+1))
    for key,row in decisions.items():
        if key not in used:refuse(row['module'],'stale-decision','unused or changed source decision',row['line'],row['column'])
    # A decision cannot create a wildcard effect grant: every effect ID must
    # resolve exactly in the explicit native/resource/guard policy data.
    effect_ids={r.get('resource_id') for r in spec['resource_policy']['rows']}
    effect_ids|={r.get('guard_id') for r in spec['guard_policy']['rows']}
    effect_ids|={hashlib.sha256(encode(r)).hexdigest() for r in spec['native_policy']['rows']}
    for row in derivation:
        for effect in row['effect_ids']:
            if effect not in effect_ids:refuse(row['module'],'unbound-effect','decision effect ID has no exact policy row',row['line'],row['column'])
    groups=[]
    for row in spec['bindings']['initialization_groups']:
        members=[name for name,item in imports.items() if item['initializer_group']==row['group_id'] and item['phase']!='L4']
        if members:groups.append(dict(row,ordinal=len(groups),modules=members))
    policies=dict(import_policy=dict(rows=list(imports.values()),ordered_sys_path=spec['bindings']['ordered_sys_path'],
                                     bootstrap_modules=spec['bindings']['bootstrap_modules']),
                  native_policy=spec['native_policy'],resource_policy=spec['resource_policy'],abi_policy=spec['abi_policy'],
                  guard_policy=spec['guard_policy'],pytest_policy=spec['pytest_policy'])
    plan=dict(schema='cho51_l_static_execution_plan_v1',groups=groups,policies=policies,bindings=spec['bindings']['host'])
    return dict(schema='cho51_l_plan_derivation_v1',status='COMPLETE_REQUIRES_INDEPENDENT_REVIEW' if not refusals else 'INCOMPLETE_REFUSED',
                plan=plan,derivation=derivation,edges=edges,refusals=refusals,
                coverage=dict(modules=len(imports),edges=len(edges),source_bytes=total_bytes,ast_nodes=source_nodes,definitions=functions),
                candidate_imports=0,third_party_imports=0,executed_code_from_inputs=0,launch_authorized=False)

def publish_plan(reader,spec,physical,outputs,checkpoint):
    """LP1 integration interface; physical is the fresh retained descriptor map."""
    result=compile_plan(spec,physical,lambda descriptor:reader.read_small(descriptor['path'],
         {key:descriptor[key] for key in ('bytes','sha256')}),checkpoint)
    # The complete derivation may exceed one bounded page. Pages are fixed-size
    # and individually reviewed, never truncated to turn an incomplete plan green.
    pages=[]
    for kind in ('derivation','edges','refusals'):
        rows=result[kind]
        for offset in range(0,len(rows),256):
            body=dict(schema='cho51_l_plan_'+kind+'_page_v1',page_index=offset//256,rows=rows[offset:offset+256])
            pages.append(dict(kind=kind,page_index=offset//256,ref=outputs.write('l-plan-'+kind+'-'+str(offset//256)+'.json',encode(body))))
    plan_ref=outputs.write('l-static-plan.json',encode(result['plan']))
    index={key:value for key,value in result.items() if key not in ('plan','derivation','edges','refusals')}
    index.update(plan_ref=plan_ref,pages=pages)
    outputs.write('l-plan-derivation-index.json',encode(index))
    return index
