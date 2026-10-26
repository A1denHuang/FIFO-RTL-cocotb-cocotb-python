# Synchronous FIFO with a cocotb testbench

A parameterized single-clock FIFO in Verilog, verified with a Python testbench
written in cocotb and simulated with Icarus Verilog. Regression runs on every
push through GitHub Actions.

## RTL

`rtl/sync_fifo.v`

| Parameter | Default | Meaning |
| --- | --- | --- |
| `DATA_WIDTH` | 8 | Width of each entry |
| `DEPTH` | 16 | Number of entries |
| `ALMOST_FULL_THRESHOLD` | `DEPTH - 2` | `almost_full` is high when occupancy >= this value |

Implementation notes:

- Circular read/write pointers plus an occupancy counter. `empty`, `full` and
  `almost_full` are decoded from the counter, so there is no extra pointer
  wrap bit.
- Active-low asynchronous reset.
- `dout` is registered: data appears on the cycle after a read is accepted, and
  holds its last value when no read happens.
- A write while `full` is dropped, unless a read is accepted in the same cycle;
  in that case both happen and the occupancy stays at `DEPTH`.
- A read while `empty` is ignored.

## Testbench

`tests/test_sync_fifo.py`

The testbench is split into a driver (drives `wr_en`/`rd_en`/`din` for one
cycle), a monitor (samples `dout` and the flags) and a scoreboard that keeps a
`collections.deque` as the reference model. After every cycle the scoreboard
checks the read data and all three flags against the model.

| Test | What it checks |
| --- | --- |
| `reset_flags_are_clean` | Flags and `dout` after reset |
| `fill_and_drain_in_order` | Fill to `full`, one extra write is dropped, drain in FIFO order |
| `almost_full_threshold` | `almost_full` rises exactly at the threshold |
| `simultaneous_read_write_keeps_order` | Read and write in the same cycle keep order and occupancy |
| `randomized_regression` | 1000 cycles of random read/write traffic (fixed seed) |

## Running

Requires Icarus Verilog and Python 3.

```bash
pip install -r requirements.txt
cd tests
make            # run all tests
make WAVES=1    # also dump waveforms
```

The CI workflow in `.github/workflows/regression.yml` runs the same `make` on
Ubuntu.

## Known limitations

- Only the default configuration (8-bit, 16 deep, threshold 14) is simulated.
  The test file hard-codes these values, so they must match the `-P` overrides
  in `tests/Makefile`.
- The random test uses one fixed seed; there is no seed sweep or functional
  coverage collection yet.
- No SystemVerilog assertions on the RTL side.
