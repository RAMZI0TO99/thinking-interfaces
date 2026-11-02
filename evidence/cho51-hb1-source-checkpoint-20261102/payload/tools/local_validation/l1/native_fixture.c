/* Benign owned transient-load target, no imports/threads/allocations. */
#include "native_observer.h"
__declspec(dllexport) unsigned long __cdecl l1_fixture_value(void) {return 0x4c315146ul;}
BOOL WINAPI DllMain(HINSTANCE instance,DWORD reason,LPVOID reserved) {
    (void)instance;(void)reason;(void)reserved;return TRUE;
}
