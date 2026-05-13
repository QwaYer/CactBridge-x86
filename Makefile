# CactBridge — ISO only (see config.mk)

include config.mk
-include config/local.mk

ifeq ($(strip $(MB2_MODULE_SRC)),)
GRUB_SRC := $(GRUB_MENU_KERNEL_ONLY)
NEED_MB2_FILE := n
else
GRUB_SRC := $(GRUB_MENU_WITH_MB2)
NEED_MB2_FILE := y
endif

.PHONY: all iso clean printconfig

all: iso

iso: $(OUT_ISO)

$(OUT_ISO): $(KERNEL_BIN) $(GRUB_SRC)
	@test -n "$(KERNEL_BIN)" || (echo "ERROR: KERNEL_BIN is empty — pass path to kernel.bin (CactOS sets it)" >&2; exit 1)
	@test -f "$(KERNEL_BIN)" || (echo "ERROR: KERNEL_BIN missing: $(KERNEL_BIN) — build the kernel first" >&2; exit 1)
	@mkdir -p $(STAGING_ROOT)/boot/grub
	cp -f "$(KERNEL_BIN)" $(STAGING_ROOT)/boot/kernel.bin
ifeq ($(NEED_MB2_FILE),y)
	@test -f "$(MB2_MODULE_SRC)" || (echo "ERROR: MB2_MODULE_SRC not a file: $(MB2_MODULE_SRC)" >&2; exit 1)
	cp -f "$(MB2_MODULE_SRC)" $(STAGING_ROOT)/boot/$(MB2_MODULE_ISO_NAME)
	sed -e 's|MB2_MODULE_PLACEHOLDER|$(MB2_MODULE_ISO_NAME)|g' \
	    -e 's|MB2_CMDLINE_PLACEHOLDER|$(MB2_MODULE_CMDLINE)|g' \
	    "$(GRUB_SRC)" > $(STAGING_ROOT)/boot/grub/grub.cfg
else
	cp -f "$(GRUB_SRC)" $(STAGING_ROOT)/boot/grub/grub.cfg
endif
	grub-mkrescue -o $(OUT_ISO) $(STAGING_ROOT)

clean:
	rm -rf $(STAGING_ROOT) $(OUT_ISO)

printconfig:
	@echo "KERNEL_BIN=$(KERNEL_BIN)"
	@echo "OUT_ISO=$(OUT_ISO)"
	@echo "MB2_MODULE_SRC=$(MB2_MODULE_SRC)"
	@echo "MB2_MODULE_ISO_NAME=$(MB2_MODULE_ISO_NAME)"
	@echo "MB2_MODULE_CMDLINE=$(MB2_MODULE_CMDLINE)"
	@echo "GRUB_SRC=$(GRUB_SRC)"
