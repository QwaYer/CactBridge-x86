# =============================================================================
# CactBridge — ISO / multiboot2 «мост» (не ядро, не initfs)
# -----------------------------------------------------------------------------
# Собирает только загрузочный образ: кладёт kernel.bin и опционально один
# произвольный файл как module2. Содержимое модуля ядру при сборке неизвестно.
#
# Переопределение: config/local.mk (gitignore) или переменные в командной строке.
# =============================================================================

KERNEL_BIN ?= $(abspath ../CactKernel-x86_32/build/kernel.bin)

# Куда положить ISO
OUT_ISO      ?= build/cact.iso
STAGING_ROOT ?= build/isodir

# Опциональный файл → копируется в ISO как /boot/$(MB2_MODULE_ISO_NAME)
# Пусто = в GRUB только multiboot2 kernel (без module2)
MB2_MODULE_SRC ?= $(abspath ../LocalRepoCactOS/cctkfs.img)
MB2_MODULE_ISO_NAME ?= payload.bin
# Строка командной модуля для Multiboot2 (ядро в mb2 ищет префикс "cctkfs" —
# это протокол рантайма, не имя репозитория initfs).
MB2_MODULE_CMDLINE ?= cctkfs

# Готовый фрагмент GRUB: с module2 или без (лежат в ./grub/)
GRUB_MENU_WITH_MB2    ?= grub/menu-with-mb2.cfg
GRUB_MENU_KERNEL_ONLY ?= grub/menu-kernel-only.cfg
