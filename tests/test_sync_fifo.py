import random
from collections import deque

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


DATA_WIDTH = 8
DEPTH = 16
ALMOST_FULL_THRESHOLD = 14
MASK = (1 << DATA_WIDTH) - 1


class FifoDriver:
    def __init__(self, dut):
        self.dut = dut

    async def reset(self):
        self.dut.rst_n.value = 0
        self.dut.wr_en.value = 0
        self.dut.rd_en.value = 0
        self.dut.din.value = 0

        for _ in range(4):
            await RisingEdge(self.dut.clk)

        self.dut.rst_n.value = 1
        await RisingEdge(self.dut.clk)

    async def cycle(self, wr_en=False, rd_en=False, din=0):
        self.dut.wr_en.value = int(wr_en)
        self.dut.rd_en.value = int(rd_en)
        self.dut.din.value = din & MASK
        await RisingEdge(self.dut.clk)
        await Timer(1, units="ps")
        self.dut.wr_en.value = 0
        self.dut.rd_en.value = 0


class FifoMonitor:
    def __init__(self, dut):
        self.dut = dut

    def flags(self):
        return {
            "empty": int(self.dut.empty.value),
            "full": int(self.dut.full.value),
            "almost_full": int(self.dut.almost_full.value),
        }

    def dout(self):
        return int(self.dut.dout.value)


class FifoScoreboard:
    def __init__(self):
        self.expected = deque()

    def apply_write(self, data):
        if len(self.expected) < DEPTH:
            self.expected.append(data & MASK)

    def apply_read(self):
        if self.expected:
            return self.expected.popleft()
        return None

    def check_flags(self, flags):
        assert flags["empty"] == int(len(self.expected) == 0)
        assert flags["full"] == int(len(self.expected) == DEPTH)
        assert flags["almost_full"] == int(len(self.expected) >= ALMOST_FULL_THRESHOLD)


async def start_fifo(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    driver = FifoDriver(dut)
    monitor = FifoMonitor(dut)
    scoreboard = FifoScoreboard()

    await driver.reset()
    scoreboard.check_flags(monitor.flags())
    return driver, monitor, scoreboard


async def fifo_step(driver, monitor, scoreboard, wr_en=False, rd_en=False, din=0):
    pre_len = len(scoreboard.expected)
    read_expected = scoreboard.expected[0] if (rd_en and pre_len > 0) else None
    write_accepted = wr_en and (pre_len < DEPTH or read_expected is not None)

    await driver.cycle(wr_en=wr_en, rd_en=rd_en, din=din)

    if read_expected is not None:
        assert monitor.dout() == read_expected
        scoreboard.apply_read()

    if write_accepted:
        scoreboard.apply_write(din)

    scoreboard.check_flags(monitor.flags())


@cocotb.test()
async def reset_flags_are_clean(dut):
    _, monitor, scoreboard = await start_fifo(dut)

    assert monitor.dout() == 0
    scoreboard.check_flags(monitor.flags())


@cocotb.test()
async def fill_and_drain_in_order(dut):
    driver, monitor, scoreboard = await start_fifo(dut)

    for value in range(DEPTH):
        await fifo_step(driver, monitor, scoreboard, wr_en=True, din=value)

    assert monitor.flags()["full"] == 1
    assert monitor.flags()["almost_full"] == 1

    await fifo_step(driver, monitor, scoreboard, wr_en=True, din=0xAA)
    assert list(scoreboard.expected) == list(range(DEPTH))

    for _ in range(DEPTH):
        await fifo_step(driver, monitor, scoreboard, rd_en=True)

    assert monitor.flags()["empty"] == 1


@cocotb.test()
async def almost_full_threshold(dut):
    driver, monitor, scoreboard = await start_fifo(dut)

    for value in range(ALMOST_FULL_THRESHOLD - 1):
        await fifo_step(driver, monitor, scoreboard, wr_en=True, din=value)

    assert monitor.flags()["almost_full"] == 0

    await fifo_step(driver, monitor, scoreboard, wr_en=True, din=0x5A)
    assert monitor.flags()["almost_full"] == 1


@cocotb.test()
async def simultaneous_read_write_keeps_order(dut):
    driver, monitor, scoreboard = await start_fifo(dut)

    for value in range(6):
        await fifo_step(driver, monitor, scoreboard, wr_en=True, din=value)

    for value in range(40, 60):
        await fifo_step(driver, monitor, scoreboard, wr_en=True, rd_en=True, din=value)

    while scoreboard.expected:
        await fifo_step(driver, monitor, scoreboard, rd_en=True)

    assert monitor.flags()["empty"] == 1


@cocotb.test()
async def randomized_regression(dut):
    driver, monitor, scoreboard = await start_fifo(dut)
    rng = random.Random(20260527)

    for _ in range(1000):
        wr_en = rng.random() < 0.58
        rd_en = rng.random() < 0.52
        din = rng.randrange(0, 1 << DATA_WIDTH)
        await fifo_step(driver, monitor, scoreboard, wr_en=wr_en, rd_en=rd_en, din=din)

    while scoreboard.expected:
        await fifo_step(driver, monitor, scoreboard, rd_en=True)

    assert monitor.flags()["empty"] == 1
