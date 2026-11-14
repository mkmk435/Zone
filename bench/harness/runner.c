/* Minimal raw-shellcode runner for the Zone benchmark.
 *
 * Reads a payload, maps it RWX, calls it with a pointer to a 256-byte result
 * buffer, and writes the buffer to a file as comma-separated hex bytes.
 * The same source is compiled for x64 and x86; the payload reads the buffer
 * pointer from RCX (x64) or [esp+4] (x86 cdecl).
 *
 * A crashing payload kills this process: the parent sees a non-zero exit code
 * and treats the run as a failure.
 */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define RESULT_SIZE 256

int main(int argc, char **argv) {
    FILE *file;
    long size;
    unsigned char *payload;
    void *memory;
    unsigned char buffer[RESULT_SIZE];
    int i;
    FILE *out;

    if (argc != 3) {
        fprintf(stderr, "usage: %s <payload> <output>\n", argv[0]);
        return 2;
    }

    file = fopen(argv[1], "rb");
    if (!file) {
        fprintf(stderr, "cannot open %s\n", argv[1]);
        return 2;
    }
    fseek(file, 0, SEEK_END);
    size = ftell(file);
    fseek(file, 0, SEEK_SET);
    if (size <= 0 || size > 1024 * 1024) {
        fclose(file);
        return 2;
    }
    payload = (unsigned char *)malloc((size_t)size);
    if (!payload) {
        fclose(file);
        return 2;
    }
    if (fread(payload, 1, (size_t)size, file) != (size_t)size) {
        fclose(file);
        free(payload);
        return 2;
    }
    fclose(file);

    memory = VirtualAlloc(NULL, (SIZE_T)size + 16,
                          MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (!memory) {
        free(payload);
        return 2;
    }
    memcpy(memory, payload, (size_t)size);
    free(payload);

    memset(buffer, 0xCC, sizeof(buffer));
    ((void (*)(void *))memory)(buffer);

    out = fopen(argv[2], "w");
    if (!out) {
        VirtualFree(memory, 0, MEM_RELEASE);
        return 2;
    }
    for (i = 0; i < RESULT_SIZE; i++) {
        fprintf(out, "%s%02x", i ? "," : "", buffer[i]);
    }
    fclose(out);
    VirtualFree(memory, 0, MEM_RELEASE);
    return 0;
}
