# FIFO RTL + Cocotb Verification

This project implements a parameterized synchronous FIFO in Verilog and verifies it with a Cocotb-based Python testbench. It is designed as a compact RTL verification portfolio project covering RTL design, randomized testing, scoreboard checking, and CI regression.

## Features

- Parameterized Verilog FIFO with configurable data width and depth
- Status flags: `empty`, `full`, and `almost_full`
- Cocotb driver, monitor, and scoreboard
- Directed tests for reset, fill, drain, almost-full threshold, overflow protection, and simultaneous read/write
- Randomized regression with a Python reference model
- GitHub Actions workflow for automatic regression

## Architecture

The FIFO uses a single clock, active-low asynchronous reset, circular read/write pointers, and an occupancy counter. Writes are accepted when the FIFO is not full, or when a valid read occurs in the same cycle. Reads are accepted when the FIFO is not empty.

```text
        wr_en/din                dout/flags
    +-------------+           +-------------+
    | Cocotb      |           | Cocotb      |
    | Driver      |---------->| Monitor     |
    +-------------+           +-------------+
            |                         |
            v                         v
    +-----------------------------------------+
    |            Verilog sync_fifo            |
    +-----------------------------------------+
            |                         |
            v                         v
    +-----------------------------------------+
    |      Python reference model + scoreboard |
    +-----------------------------------------+
```

## Repository Layout

```text
.
+-- rtl/
|   +-- sync_fifo.v
+-- tests/
|   +-- Makefile
|   +-- test_sync_fifo.py
+-- .github/workflows/
|   +-- regression.yml
+-- requirements.txt
+-- README.md
```

## Run Locally

Install Icarus Verilog first, then run:

```bash
pip install -r requirements.txt
cd tests
make
```

To view waveforms, run with tracing enabled:

```bash
cd tests
make WAVES=1
```

## Verification Scenarios

- Reset initializes flags and output state
- FIFO fills to `full` without losing data
- Extra writes while full do not corrupt stored entries
- FIFO drains in first-in, first-out order
- `almost_full` asserts at the configured threshold
- Simultaneous read/write preserves ordering and occupancy
- Randomized read/write traffic is checked against a Python `deque` reference model

## Resume Keywords

`RTL`, `Verilog`, `Python`, `Cocotb`, `testbench`, `driver`, `monitor`, `scoreboard`, `random regression`, `GitHub Actions`

## Interview Talking Points

- The FIFO is implemented with circular pointers plus a count register, making `empty`, `full`, and `almost_full` straightforward to derive.
- The Cocotb testbench mirrors UVM-style structure with a driver, monitor, and scoreboard, but keeps the implementation lightweight in Python.
- The scoreboard acts as the golden model and catches ordering, overflow, underflow, and simultaneous read/write bugs.
- CI regression makes the project reproducible and demonstrates verification automation rather than one-off simulation.
