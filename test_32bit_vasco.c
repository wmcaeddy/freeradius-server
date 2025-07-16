#include <stdio.h>
#include <stdlib.h>
#include <dlfcn.h>

int main() {
    printf("Testing 32-bit VASCO library loading...\n");
    
    // Try to load the VASCO library
    void *handle = dlopen("/opt/vasco/libaal2sdk.so", RTLD_LAZY);
    
    if (!handle) {
        printf("✗ Failed to load VASCO library: %s\n", dlerror());
        return 1;
    }
    
    printf("✓ VASCO library loaded successfully\n");
    printf("Library handle: %p\n", handle);
    
    // Try to find actual VASCO function names
    char *functions[] = {
        "AAL2VerifyPassword",
        "AAL2VerifyPasswordEx",
        "AAL2VerifyAll",
        "AAL2DPXInit",
        "AAL2DPXClose",
        "AAL2DPXGetToken",
        "AAL2AuthorizeUnlock",
        NULL
    };
    
    for (int i = 0; functions[i] != NULL; i++) {
        void *func = dlsym(handle, functions[i]);
        if (func) {
            printf("✓ Found function: %s at %p\n", functions[i], func);
        } else {
            printf("✗ Function not found: %s\n", functions[i]);
        }
    }
    
    // Clean up
    dlclose(handle);
    printf("✓ Library closed successfully\n");
    
    return 0;
}