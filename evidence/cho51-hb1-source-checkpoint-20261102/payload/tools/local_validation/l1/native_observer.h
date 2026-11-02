#ifndef CHO51_L1_NATIVE_H
#define CHO51_L1_NATIVE_H
/* Deliberately header-closed Windows x64 ABI. Q must verify all sizes/offsets
 * and compile with the exact reviewed x86_64-pc-windows-msvc target. */
#if !defined(_WIN64) || !defined(_M_X64)
#error L1 requires reviewed Windows x64 target
#endif
typedef unsigned short uint16_t;
typedef unsigned int uint32_t;
typedef unsigned long long uint64_t;
typedef unsigned long long uintptr_t;
typedef int BOOL;
typedef unsigned long DWORD;
typedef unsigned long ULONG;
typedef unsigned short USHORT;
typedef long LONG;
typedef void *PVOID;
typedef void *LPVOID;
typedef void *HANDLE;
typedef void *HMODULE;
typedef void *HINSTANCE;
typedef unsigned short *PWSTR;
typedef unsigned short *LPWSTR;
typedef const unsigned short *LPCWSTR;
#define CALLBACK __stdcall
#define WINAPI __stdcall
#define NTAPI __stdcall
#define TRUE 1
#define LIST_MODULES_ALL 3u
typedef struct MODULEINFO {PVOID lpBaseOfDll; DWORD SizeOfImage; PVOID EntryPoint;} MODULEINFO;
__declspec(dllimport) HMODULE WINAPI GetModuleHandleW(LPCWSTR);
__declspec(dllimport) PVOID WINAPI GetProcAddress(HMODULE,const char*);
__declspec(dllimport) HANDLE WINAPI GetCurrentProcess(void);
__declspec(dllimport) BOOL WINAPI K32EnumProcessModulesEx(HANDLE,HMODULE*,DWORD,DWORD*,DWORD);
__declspec(dllimport) BOOL WINAPI K32GetModuleInformation(HANDLE,HMODULE,MODULEINFO*,DWORD);
__declspec(dllimport) DWORD WINAPI K32GetModuleFileNameExW(HANDLE,HMODULE,LPWSTR,DWORD);
long _InterlockedOr(long volatile *,long);
long _InterlockedIncrement(long volatile *);
long _InterlockedDecrement(long volatile *);
long _InterlockedCompareExchange(long volatile *,long,long);
void _ReadWriteBarrier(void);
#define L1_ABI 1u
#define L1_EVENTS 8192u
#define L1_IMAGES 4096u
#define L1_PATH 1024u
#define L1_FAULT_OVERFLOW 1u
#define L1_FAULT_REASON 2u
#define L1_FAULT_STRING 4u
#define L1_FAULT_STATE 8u
typedef struct L1Event {
    uint64_t sequence, base, generation;
    uint32_t reason, image_size, path_units, faults;
    uint16_t path[L1_PATH];
} L1Event;
typedef struct L1Image {
    uint64_t base;
    uint32_t image_size, path_units;
    uint16_t path[L1_PATH];
} L1Image;
typedef struct L1State {
    uint32_t abi, event_size, image_size, state_size;
    uint32_t started, stopped, active_callbacks, faults;
    uint32_t produced, consumed, capacity, path_capacity;
    uint64_t generation;
} L1State;
#define L1_API __declspec(dllexport) int __cdecl
#ifdef L1_OBSERVER_IMPLEMENTATION
L1_API l1_start(uint32_t abi,uint64_t generation);
L1_API l1_drain(L1Event *out,uint32_t capacity,uint32_t *count,uint32_t *faults);
L1_API l1_snapshot(L1Image *out,uint32_t capacity,uint32_t *count);
L1_API l1_stop(uint32_t *faults);
L1_API l1_state(L1State *out);
#endif
#endif
