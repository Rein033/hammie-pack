/* SPDX-License-Identifier: MIT */
#include "khal_crc32.h"
uint32_t khal_crc32(uint32_t crc, const void *buf, size_t len)
{
    const unsigned char *p = buf;
    crc = ~crc;
    while (len--) { crc ^= *p++; for (int k = 0; k < 8; k++) crc = (crc >> 1) ^ (0xEDB88320u & (0u - (crc & 1u))); }
    return ~crc;
}
