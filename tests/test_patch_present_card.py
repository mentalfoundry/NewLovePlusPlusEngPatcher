"""Date present picker: English header and "Bought 11/21" purchase line."""

from __future__ import annotations

import faulthandler
import struct
import sys

import pytest
from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from conftest import SRC, load_module

card = load_module("patch_present_card", SRC / "patch_present_card.py")

VA = 0x100000


def _image() -> bytearray:
    data = bytearray(card.ADDR_HEADER + len(card.VANILLA_HEADER) + 16)
    data[card.ADDR_ARGS : card.ADDR_ARGS + len(card.VANILLA_ARGS)] = card.VANILLA_ARGS
    data[card.ADDR_FORMAT : card.ADDR_FORMAT + len(card.VANILLA_FORMAT)] = card.VANILLA_FORMAT
    data[card.ADDR_HEADER : card.ADDR_HEADER + len(card.VANILLA_HEADER)] = card.VANILLA_HEADER
    return data


def test_args_keep_the_format_pc_and_disassemble():
    insns = list(Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(card.build_args(), card.ADDR_ARGS))
    assert [(i.mnemonic, i.op_str) for i in insns] == [
        ("add", "r3, r1, r5, lsl #2"),
        ("ldr", "r3, [r3, #0xc]"),
        ("str", "r3, [sp]"),
        ("str", "r2, [sp, #4]"),
        ("add", "r2, pc, #0xcc"),
        ("mov", "r3, sl"),
    ]
    assert card.ADDR_ARGS + 16 + 8 + 0xCC == card.ADDR_FORMAT


def test_slots_keep_their_size_and_print_bought_date():
    assert len(card.build_format()) == 12 and len(card.build_header()) == 56
    assert card.build_header().split(b"\x00")[0] == b"Choose a present to bring"
    text = card.FORMAT.decode() % ("Bought", 12, 31)
    assert text == "Bought 12/31" and len(text) + 1 <= 0x20
    with pytest.raises(ValueError, match="slot is 4"):
        card._slot(b"toolong", 4)


def test_apply_is_idempotent_and_guards_every_site():
    data = _image()
    assert card.apply_patch(data) is True
    assert card.is_patched(data)
    assert card.apply_patch(data) is False
    for off in (card.ADDR_ARGS, card.ADDR_FORMAT, card.ADDR_HEADER):
        bad = _image()
        bad[off] ^= 0xA5
        before = bytes(bad)
        with pytest.raises(ValueError, match=f"{off:#x}"):
            card.apply_patch(bad)
        assert bytes(bad) == before  # nothing written


def test_args_pass_bought_month_day_to_snprintf():
    unicorn = pytest.importorskip("unicorn")
    from unicorn.arm_const import (
        UC_ARM_REG_R1,
        UC_ARM_REG_R2,
        UC_ARM_REG_R3,
        UC_ARM_REG_R5,
        UC_ARM_REG_R10,
        UC_ARM_REG_SP,
    )

    code_base, table, stack = 0x68000, 0x200000, 0x300000
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    was_on = faulthandler.is_enabled()
    faulthandler.disable()  # see test_patch_syspopup_tall_text.py
    try:
        uc.mem_map(code_base, 0x1000)
        uc.mem_map(table, 0x1000)
        uc.mem_map(stack, 0x1000)
    finally:
        if was_on:
            faulthandler.enable(file=sys.__stderr__)
    args = card.build_args()
    uc.mem_write(card.ADDR_ARGS, args)
    slot = 2  # card index r5; each record is 0xb4 bytes (r5 = idx * 45)
    r5 = slot * 45
    uc.mem_write(table + 0xC + r5 * 4, struct.pack("<I", 11))  # month
    uc.reg_write(UC_ARM_REG_R1, table)
    uc.reg_write(UC_ARM_REG_R5, r5)
    uc.reg_write(UC_ARM_REG_R2, 21)  # day, loaded before the window
    uc.reg_write(UC_ARM_REG_R10, 0xB0B0)  # 購入 string
    uc.reg_write(UC_ARM_REG_SP, stack + 0x100)
    uc.emu_start(card.ADDR_ARGS, card.ADDR_ARGS + len(args))
    assert uc.reg_read(UC_ARM_REG_R3) == 0xB0B0
    assert uc.reg_read(UC_ARM_REG_R2) == card.ADDR_FORMAT
    assert struct.unpack("<2I", bytes(uc.mem_read(stack + 0x100, 8))) == (11, 21)
