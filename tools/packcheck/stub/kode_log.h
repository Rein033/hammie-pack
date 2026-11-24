#pragma once
#include <stdio.h>
#define KLOG_E(t, ...) (fprintf(stderr, "E %s: ", t), fprintf(stderr, __VA_ARGS__), fputc(10, stderr))
#define KLOG_W(t, ...) (fprintf(stderr, "W %s: ", t), fprintf(stderr, __VA_ARGS__), fputc(10, stderr))
#define KLOG_N(t, ...) (fprintf(stderr, "N %s: ", t), fprintf(stderr, __VA_ARGS__), fputc(10, stderr))
#define KLOG_I(t, ...) (fprintf(stderr, "I %s: ", t), fprintf(stderr, __VA_ARGS__), fputc(10, stderr))
#define KLOG_D(t, ...) ((void)0)
#include <stdarg.h>
enum { KODE_LOG_DEBUG, KODE_LOG_INFO, KODE_LOG_NOTICE, KODE_LOG_WARN, KODE_LOG_ERROR };
static inline void kode_log(int lvl, const char *tag, const char *fmt, ...)
{ if (lvl < KODE_LOG_WARN) return; va_list ap; va_start(ap, fmt); fprintf(stderr, "%s %s: ", lvl == KODE_LOG_WARN ? "W" : "E", tag); vfprintf(stderr, fmt, ap); fputc(10, stderr); va_end(ap); }
