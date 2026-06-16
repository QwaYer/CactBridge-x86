# 💾 CactBridge

<p align="center">
  <img src="https://img.shields.io/badge/license-GPLv3-blue.svg?style=for-the-badge" alt="License: GPLv3">
  <img src="https://img.shields.io/badge/role-ISO%20packager-purple.svg?style=for-the-badge" alt="Role: ISO packager">
  <img src="https://img.shields.io/badge/output-cact.iso-green.svg?style=for-the-badge" alt="Output: cact.iso">
  <img src="https://img.shields.io/badge/boot-Multiboot2-orange.svg?style=for-the-badge" alt="Boot: Multiboot2">
  <img src="https://img.shields.io/badge/version-2.0.0-yellow.svg?style=for-the-badge" alt="2.0.0">
</p>

<p align="center">
  <strong>English.</strong> ISO packager: copies a prebuilt <strong><code>kernel.bin</code></strong> and an optional <strong>Multiboot2 <code>module2</code></strong> (e.g. <strong><code>cctkfs.img</code></strong>) into a staging tree and runs <strong><code>grub-mkrescue</code></strong>.<br>
  <strong>2.0.0:</strong> rewritten from Makefile to <strong><code>build.py</code></strong>. Supports <code>--gui-iso</code>, <code>--non-gui-iso</code>, <code>--no-deps</code> flags. Auto-detects sibling repos.<br>
  <strong>Русский.</strong> «Мост» для сборки <strong>ISO</strong>: <strong><code>build.py</code></strong> оркестрирует ядро, модули и <strong><code>grub-mkrescue</code></strong>.<br>
  <strong>2.0.0:</strong> переписан с Makefile на <strong><code>build.py</code></strong> с поддержкой GUI и non-GUI сборок.
</p>

---

## 🔗 Ecosystem

| Piece | Role |
| --- | --- |
| **[CactOS-x86_32](https://github.com/QwaYer/CactOS-x86_32)** | Invokes **`build.py`** with `--non-gui-iso` or `--gui-iso` |
| **[CactKernel-x86_32](https://github.com/QwaYer/CactKernel-x86_32)** | Produces **`build/kernel.bin`** |
| **LocalRepoCactOS** | Produces **`cctkfs.img`** |

---

## 🔨 Building

**Recommended — full workspace**

From the workspace parent:

```sh
make -C CactOS-x86_32 iso       # build.py --non-gui-iso
make -C CactOS-x86_32 iso-gui   # build.py --gui-iso
```

**Standalone — this repository**

```sh
python3 build.py                # auto-detects kernel.bin + cctkfs.img
```

Overrides via `config/local.mk.py` (see `config/local.mk.example`).

```sh
python3 build.py --help         # show available flags
python3 build.py --non-gui-iso  # non-GUI ISO
python3 build.py --gui-iso      # GUI ISO
python3 build.py --no-deps      # skip rebuild, repack only
```

---

## 📂 Layout

```
CactBridge/
├── build.py               # ISO builder — orchestrates make in siblings + grub-mkrescue
├── config/
│   └── local.mk.example   # example local overrides
├── grub/
│   ├── menu-with-mb2.cfg
│   └── menu-kernel-only.cfg
└── build/                 # staging + cact.iso (generated)
```
