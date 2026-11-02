/* Native loader notification observer. No runtime/allocator in callback.
 * The generated callback and all inlined callees MUST be inspected in Q.
 * Fixed append-only storage: never overwrite or silently drop an event.
 * No restart: a consumed observer generation belongs to one owned process.
 */
#define L1_OBSERVER_IMPLEMENTATION 1
#include "native_observer.h"
#pragma intrinsic(_InterlockedOr)
#pragma intrinsic(_InterlockedIncrement)
#pragma intrinsic(_InterlockedDecrement)
#pragma intrinsic(_InterlockedCompareExchange)
#pragma intrinsic(_ReadWriteBarrier)
typedef struct L1Unicode { USHORT Length, MaximumLength; PWSTR Buffer; } L1Unicode;
typedef struct L1Notification {
    ULONG Flags;
    const L1Unicode *FullDllName, *BaseDllName;
    PVOID DllBase;
    ULONG SizeOfImage;
} L1Notification;
typedef void (CALLBACK *L1Callback)(ULONG,const L1Notification*,PVOID);
typedef LONG (NTAPI *RegisterFn)(ULONG,L1Callback,PVOID,PVOID*);
typedef LONG (NTAPI *UnregisterFn)(PVOID);
static L1Event events[L1_EVENTS];
static volatile LONG produced, consumed, fault_bits, active_callbacks, started, stopped;
static uint64_t observer_generation;
static PVOID cookie;
static RegisterFn register_fn;
static UnregisterFn unregister_fn;
static HMODULE snapshot_modules[L1_IMAGES];

/* No calls, allocation, locks, logging or libc are permitted in this function.
 * Windows owns pointer lifetime for the duration of the notification. Length,
 * MaximumLength, null and surrogate checks bound every copied UTF16 unit.
 */
static __declspec(noinline) void CALLBACK l1_notification(ULONG reason,const L1Notification *data,PVOID context) {
    LONG slot;
    uint32_t i,n;
    const L1Unicode *name;
    const uint16_t *source;
    L1Event *event;
    (void)context;
    _InterlockedIncrement(&active_callbacks);
    if (started!=1 || stopped!=0) {
        _InterlockedOr(&fault_bits,L1_FAULT_STATE);
        _InterlockedDecrement(&active_callbacks);
        return;
    }
    if ((reason!=1 && reason!=2) || !data) {
        _InterlockedOr(&fault_bits,L1_FAULT_REASON);
        _InterlockedDecrement(&active_callbacks);
        return;
    }
    name=data->FullDllName;
    if (!name || !name->Buffer || !name->Length || (name->Length&1)
        || name->Length>name->MaximumLength || name->Length>=L1_PATH*2
        || !data->DllBase || !data->SizeOfImage) {
        _InterlockedOr(&fault_bits,L1_FAULT_STRING);
        _InterlockedDecrement(&active_callbacks);
        return;
    }
    n=name->Length/2;
    source=(const uint16_t*)name->Buffer;
    for(i=0;i<n;i++) {
        uint16_t c=source[i];
        if (!c || (c>=0xDC00 && c<=0xDFFF)) {
            _InterlockedOr(&fault_bits,L1_FAULT_STRING);
            _InterlockedDecrement(&active_callbacks);
            return;
        }
        if (c>=0xD800 && c<=0xDBFF) {
            if (i+1>=n || source[i+1]<0xDC00 || source[i+1]>0xDFFF) {
                _InterlockedOr(&fault_bits,L1_FAULT_STRING);
                _InterlockedDecrement(&active_callbacks);
                return;
            }
            i++;
        }
    }
    /* Loader notifications are serialized by the Windows loader lock. CAS
       additionally detects unexpected concurrent/reentrant production. */
    slot=produced;
    if (slot<0 || slot>=(LONG)L1_EVENTS) {
        _InterlockedOr(&fault_bits,L1_FAULT_OVERFLOW);
        _InterlockedDecrement(&active_callbacks);
        return;
    }
    event=&events[slot];
    event->sequence=(uint64_t)slot+1;
    event->base=(uint64_t)(uintptr_t)data->DllBase;
    event->generation=observer_generation;
    event->reason=reason;
    event->image_size=data->SizeOfImage;
    event->path_units=n;
    event->faults=0;
    for(i=0;i<n;i++) event->path[i]=source[i];
    event->path[n]=0;
    _ReadWriteBarrier();
    if (_InterlockedCompareExchange(&produced,slot+1,slot)!=slot)
        _InterlockedOr(&fault_bits,L1_FAULT_STATE);
    _InterlockedDecrement(&active_callbacks);
}

L1_API l1_start(uint32_t abi,uint64_t generation) {
    HMODULE ntdll;
    LONG status;
    if(abi!=L1_ABI || !generation || started || stopped) return 0;
    ntdll=GetModuleHandleW(L"ntdll.dll");
    if(!ntdll) return 0;
    register_fn=(RegisterFn)(uintptr_t)GetProcAddress(ntdll,"LdrRegisterDllNotification");
    unregister_fn=(UnregisterFn)(uintptr_t)GetProcAddress(ntdll,"LdrUnregisterDllNotification");
    if(!register_fn || !unregister_fn) return 0;
    observer_generation=generation;
    _InterlockedCompareExchange(&started,1,0);
    status=register_fn(0,l1_notification,0,&cookie);
    if(status<0 || !cookie) {
        _InterlockedOr(&fault_bits,L1_FAULT_STATE);
        _InterlockedCompareExchange(&stopped,1,0);
        return 0;
    }
    return 1;
}
L1_API l1_drain(L1Event *out,uint32_t capacity,uint32_t *count,uint32_t *faults) {
    uint32_t i,n,j;
    LONG first=consumed, last=produced;
    if(!out || !count || !faults || !capacity || capacity>L1_EVENTS || !started || first<0 || last<first) return 0;
    n=(uint32_t)(last-first); if(n>capacity)n=capacity;
    for(i=0;i<n;i++) {
        /* Explicit member copies avoid compiler struct-copy dependency here;
           callback inspection remains mandatory independently. */
        L1Event *a=&out[i],*b=&events[first+i];
        a->sequence=b->sequence; a->base=b->base; a->generation=b->generation;
        a->reason=b->reason; a->image_size=b->image_size; a->path_units=b->path_units; a->faults=b->faults;
        for(j=0;j<=b->path_units;j++)a->path[j]=b->path[j];
    }
    consumed=first+(LONG)n; *count=n; *faults=(uint32_t)fault_bits;
    return fault_bits==0;
}
L1_API l1_snapshot(L1Image *out,uint32_t capacity,uint32_t *count) {
    DWORD needed=0,i,n;
    HANDLE process=GetCurrentProcess();
    if(!out || !count || capacity!=L1_IMAGES || !started) return 0;
    if(!K32EnumProcessModulesEx(process,snapshot_modules,sizeof(snapshot_modules),&needed,LIST_MODULES_ALL)
       || needed%sizeof(HMODULE) || needed>sizeof(snapshot_modules)) return 0;
    n=needed/sizeof(HMODULE);
    for(i=0;i<n;i++) {
        MODULEINFO info;
        DWORD length;
        if(!K32GetModuleInformation(process,snapshot_modules[i],&info,sizeof(info)))return 0;
        length=K32GetModuleFileNameExW(process,snapshot_modules[i],(LPWSTR)out[i].path,L1_PATH);
        if(!length || length>=L1_PATH || !info.lpBaseOfDll || !info.SizeOfImage)return 0;
        out[i].base=(uint64_t)(uintptr_t)info.lpBaseOfDll;
        out[i].image_size=info.SizeOfImage; out[i].path_units=length;
    }
    *count=n; return 1;
}
L1_API l1_stop(uint32_t *faults) {
    LONG status;
    if(!faults || !started || stopped || !cookie || !unregister_fn)return 0;
    status=unregister_fn(cookie);
    if(status<0) {_InterlockedOr(&fault_bits,L1_FAULT_STATE);*faults=(uint32_t)fault_bits;return 0;}
    cookie=0; _InterlockedCompareExchange(&stopped,1,0);
    if(active_callbacks)_InterlockedOr(&fault_bits,L1_FAULT_STATE);
    *faults=(uint32_t)fault_bits;
    return active_callbacks==0 && fault_bits==0;
}
L1_API l1_state(L1State *out) {
    if(!out)return 0;
    out->abi=L1_ABI;out->event_size=sizeof(L1Event);out->image_size=sizeof(L1Image);out->state_size=sizeof(L1State);
    out->started=(uint32_t)started;out->stopped=(uint32_t)stopped;out->active_callbacks=(uint32_t)active_callbacks;
    out->faults=(uint32_t)fault_bits;out->produced=(uint32_t)produced;out->consumed=(uint32_t)consumed;
    out->capacity=L1_EVENTS;out->path_capacity=L1_PATH;out->generation=observer_generation;return 1;
}
BOOL WINAPI DllMain(HINSTANCE instance,DWORD reason,LPVOID reserved) {
    (void)instance;(void)reason;(void)reserved;return TRUE;
}
#ifdef L1_FIXTURE
/* Compile a distinct fixture binary. These exports MUST NOT exist in the L
 * production helper. Q drives synthetic names without external operations. */
L1_API l1_fixture_notify(uint32_t reason,const uint16_t *path,uint32_t units,uint64_t base,uint32_t size) {
    L1Unicode name;
    L1Notification notification;
    if(units>32767)return 0;
    name.Length=(USHORT)(units*2);name.MaximumLength=name.Length;name.Buffer=(PWSTR)path;
    notification.Flags=0;notification.FullDllName=&name;notification.BaseDllName=&name;
    notification.DllBase=(PVOID)(uintptr_t)base;notification.SizeOfImage=size;
    l1_notification(reason,&notification,0);return 1;
}
#endif
