#pragma once
#include <stdlib.h>
static inline void *khal_alloc_psram(size_t n, size_t size) { return calloc(n, size); }
static inline void khal_free(void *p) { free(p); }
