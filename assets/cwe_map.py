crash_type_to_cwe = {
    'Use-of-uninitialized-value' : 457, # Use of Uninitialized Variable
    'UNKNOWN WRITE' : 787, # Out-of-bounds Write
    'Heap-buffer-overflow' : 122, # Heap-based Buffer Overflow
    'Index-out-of-bounds' : 129, # Improper Validation of Array Index
    'Stack-buffer-overflow' : 121, # Stack-based Buffer Overflow
    'UNKNOWN READ' : 125, # Out-of-bounds Read
    'Global-buffer-overflow' : 120, # Buffer Copy without Checking Size of Input
    'Use-after-poison' : 416, # Might be wrong
    'Heap-use-after-free' : 416, # Use After Free
    'Bad-free': 416,
    'Negative-size-param' : 1284, # Improper Size Validation
    'Segv on unknown address' : 476, # NULL Pointer Dereference
    'Null-dereference' : 476,
    'Heap-double-free' : 415, # Double Free
    'Invalid-free' : 590, # Free of Memory not on the Heap
    'Memcpy-param-overlap' : 475, # Argument with Incorrect Length
    'Stack-use-after-return' : 562,  # Return of Stack Variable Address
    'Stack-buffer-underflow' : 124  # Buffer Underwrite ('Buffer Underflow')
}

# from cwe.mitre.org, description
cwe_id_to_desc = {
    457: "The code uses a variable that has not been initialized, leading to unpredictable or unintended results",
    787: "The product writes data past the end, or before the beginning, of the intended buffer",
    122: "A heap overflow condition is a buffer overflow, where the buffer that can be overwritten is allocated in the heap portion of memory, generally meaning that the buffer was allocated using a routine such as malloc()",
    129: "The product uses untrusted input when calculating or using an array index, but the product does not validate or incorrectly validates the index to ensure the index references a valid position within the array",
    121: "A stack-based buffer overflow condition is a condition where the buffer being overwritten is allocated on the stack (i.e., is a local variable or, rarely, a parameter to a function)",
    125: "The product reads data past the end, or before the beginning, of the intended buffer",
    120: "The product copies an input buffer to an output buffer without verifying that the size of the input buffer is less than the size of the output buffer, leading to a buffer overflow",
    416: "The product reuses or references memory after it has been freed. At some point afterward, the memory may be allocated again and saved in another pointer, while the original pointer references a location somewhere within the new allocation. Any operations using the original pointer are no longer valid because the memory \"belongs\" to the code that operates on the new pointer",
    1284: "The product receives input that is expected to specify a quantity (such as size or length), but it does not validate or incorrectly validates that the quantity has the required properties",
    476: "The product dereferences a pointer that it expects to be valid but is NULL",
    415: "The product calls free() twice on the same memory address, potentially leading to modification of unexpected memory locations",
    590: "The product calls free() on a pointer to memory that was not allocated using associated heap allocation functions such as malloc(), calloc(), or realloc()",
    475: "The behavior of this function is undefined unless its control parameter is set to a specific value",
    562: "A function returns the address of a stack variable, which will cause unintended program behavior, typically in the form of a crash",
    124: "The product writes to a buffer using an index or pointer that references a memory location prior to the beginning of the buffer"
}
