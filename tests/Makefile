TOPLEVEL_LANG = verilog
SIM ?= icarus

PWD := $(shell pwd)

VERILOG_SOURCES = $(PWD)/../rtl/sync_fifo.v
TOPLEVEL = sync_fifo
MODULE = test_sync_fifo

COMPILE_ARGS += -Psync_fifo.DATA_WIDTH=8
COMPILE_ARGS += -Psync_fifo.DEPTH=16
COMPILE_ARGS += -Psync_fifo.ALMOST_FULL_THRESHOLD=14

include $(shell cocotb-config --makefiles)/Makefile.sim
