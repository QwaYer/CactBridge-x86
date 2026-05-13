# 💾 CactBridge

<p align="center">
  <img src="https://img.shields.io/badge/license-GPLv3-blue.svg?style=for-the-badge" alt="License: GPLv3">
  <img src="https://img.shields.io/badge/role-ISO%20packager-purple.svg?style=for-the-badge" alt="Role: ISO packager">
  <img src="https://img.shields.io/badge/output-cact.iso-green.svg?style=for-the-badge" alt="Output: cact.iso">
  <img src="https://img.shields.io/badge/boot-Multiboot2-orange.svg?style=for-the-badge" alt="Boot: Multiboot2">
</p>

<p align="center">
  <strong>English.</strong> Small <strong>GRUB</strong> front-end: copies a prebuilt <strong><code>kernel.bin</code></strong> and an optional <strong>Multiboot2 <code>module2</code></strong> (e.g. <strong><code>cctkfs.img</code></strong>) into a staging tree and runs <strong><code>grub-mkrescue</code></strong>.<br>
  <strong>Русский.</strong> «Мост» только для <strong>ISO</strong>: кладёт <strong><code>kernel.bin</code></strong> и опционально модуль <strong><code>cctkfs.img</code></strong>, вызывает <strong><code>grub-mkrescue</code></strong> — не ядро и не userland.
</p>

---

## 🔗 Ecosystem

| Piece | Role |
| --- | --- |
| **[CactOS-x86_32](https://github.com/QwaYer/CactOS-x86_32)** | Calls **`make iso`** here with **`KERNEL_BIN`**, **`MB2_MODULE_SRC`**, … |
| **[CactKernel-x86_32](https://github.com/QwaYer/CactKernel-x86_32)** | Produces **`build/kernel.bin`** |
| **LocalRepoCactOS** | Produces **`cctkfs.img`** |

---

## 🔨 Building

**Recommended — full workspace**

From the workspace parent:

```sh
make -C CactOS-x86_32 iso
```

**Standalone — this repository**

```sh
make iso    # auto-detects ../CactKernel-x86_32/build/kernel.bin + ../LocalRepoCactOS/cctkfs.img
```

Override any path if needed: `make iso KERNEL_BIN=/custom/kernel.bin MB2_MODULE_SRC=`. See [`config.mk`](config.mk).

```sh
make clean
make printconfig   # show resolved paths
```

---

## 📂 Layout

```
CactBridge/
├── Makefile
├── config.mk
├── config/local.mk.example
├── grub/
└── build/           # staging + cact.iso (generated)
```
