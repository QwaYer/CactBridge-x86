S := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
.DEFAULT_GOAL := help

help:
	@echo "CactOS workspace — see README.md"
	@echo ""
	@echo "Quick:  ./build-cact-qemu.sh"
	@echo "        or  make -C CactOS-x86_32 -j\$$(nproc)"
	@echo ""
	@echo "make -C CactOS-x86_32 iso      full ISO (default)"
	@echo "make -C CactOS-x86_32 disk     ISO + nvme.img"
	@echo "make -C CactOS-x86_32 kernel   kernel only"
	@echo "make -C CactOS-x86_32 libc     libc only"
	@echo "make -C CactOS-x86_32 drivers  out-of-tree drivers"
	@echo "make -C CactOS-x86_32 clean    clean all"

%:
	@$(MAKE) -C "$(S)CactOS-x86_32" $@
