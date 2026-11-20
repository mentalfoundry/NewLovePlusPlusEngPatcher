#!/usr/bin/env python3
"""Present picker before a date: English header and "Bought 11/21".

Phone > Call Out (or any date) opens a picker for the present to bring.
Both strings on it live in ``code.bin``, not the TRB:

* The header bar is the UTF-8 literal 「持っていくプレゼントを選んでください」
  @ file ``0x68be8`` (``add r2, pc`` @ ``0x68b74``). It becomes
  "Choose a present to bring" in the same 56-byte slot.
* Each card's purchase line is ``snprintf(buf, 0x20, "%d%s%d%s %s", month,
  月, day, 日, 購入)`` @ ``0x688bc``. The three words come from TextResource
  ``FUN_005c0d4c(0x9400, n, 1)``, and 月/日 are the shared units ("Month",
  " Day(s)"), so it printed "11Month21 Day(s) Bought". The argument setup
  @ ``0x6889c`` now passes ``(購入, month, day)`` and the 12-byte format
  @ ``0x68980`` becomes ``"%s %d/%d"``: "Bought 11/21". The 月/日 lookups
  still run; their results are unused.

All in place, no caves.
"""
from __future__ import annotations

import struct

ADDR_ARGS = 0x0006889C  # 6 words before add r0, r1, sb; mov r1, #0x20; blx snprintf
ADDR_FORMAT = 0x00068980
ADDR_HEADER = 0x00068BE8

VANILLA_ARGS = bytes.fromhex(
    "0ca08de5"  # str sl, [sp, #0xc]       購入
    "05088de8"  # stm sp, {r0, r2, fp}     月, day, 日
    "0c00a0e3"  # mov r0, #0xc
    "050180e0"  # add r0, r0, r5, lsl #2
    "cc208fe2"  # add r2, pc, #0xcc        format
    "003091e7"  # ldr r3, [r1, r0]         month
)
VANILLA_FORMAT = b"%d%s%d%s %s\x00"
VANILLA_HEADER = "持っていくプレゼントを選んでください".encode() + b"\x00\x00"

FORMAT = b"%s %d/%d"
HEADER = b"Choose a present to bring"


def _u32(x: int) -> bytes:
    return struct.pack("<I", x & 0xFFFFFFFF)


def build_args() -> bytes:
    """snprintf(buf, 0x20, fmt, 購入, month, day)."""
    code = (
        _u32(0xE0813105)  # add r3, r1, r5, lsl #2
        + _u32(0xE593300C)  # ldr r3, [r3, #0xc]      month
        + _u32(0xE58D3000)  # str r3, [sp]
        + _u32(0xE58D2004)  # str r2, [sp, #4]         day
        + VANILLA_ARGS[16:20]  # add r2, pc, #0xcc     format (same pc)
        + _u32(0xE1A0300A)  # mov r3, sl               購入
    )
    assert len(code) == len(VANILLA_ARGS)
    return code


def _slot(text: bytes, size: int) -> bytes:
    if len(text) + 1 > size:
        raise ValueError(f"{text!r} needs {len(text) + 1} bytes, slot is {size}")
    return text + b"\x00" * (size - len(text))


def build_format() -> bytes:
    return _slot(FORMAT, len(VANILLA_FORMAT))


def build_header() -> bytes:
    return _slot(HEADER, len(VANILLA_HEADER))


def _sites() -> tuple[tuple[int, bytes, bytes], ...]:
    return (
        (ADDR_ARGS, VANILLA_ARGS, build_args()),
        (ADDR_FORMAT, VANILLA_FORMAT, build_format()),
        (ADDR_HEADER, VANILLA_HEADER, build_header()),
    )


def is_patched(data: bytes) -> bool:
    return all(data[off : off + len(new)] == new for off, _old, new in _sites())


def apply_patch(data: bytearray) -> bool:
    if is_patched(data):
        print("[present-card] already applied")
        return False
    for off, old, _new in _sites():
        have = bytes(data[off : off + len(old)])
        if have != old:
            raise ValueError(f"unexpected bytes @{off:#x}: {have[:8].hex()}")
    for off, _old, new in _sites():
        data[off : off + len(new)] = new
    print(f"[present-card] header {HEADER.decode()!r}, purchase line {FORMAT.decode()!r}")
    return True
