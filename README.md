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

One command installs missing dependencies and builds kernel + cctkfs.img + ISO:

```sh
./build.sh            # check deps, install missing, build everything
./build.sh --deps     # install/detect dependencies only (pacman + rustup nightly)
./build.sh --build    # build only (deps already installed)
./build.sh --run      # build, then launch QEMU
./build.sh --clean    # clean build artefacts
```

Required packages (installed automatically via `pacman`): `base-devel`, `binutils`,
`nasm`, `grub`, `xorriso`, `mtools`, `python`, `e2fsprogs`, `rustup`.
`rustup` is then configured to **nightly** with the `rust-src` component, which the
kernel's Rust subsystems (`-Z build-std`) require. Building needs network access
for the ACPICA clone and the `crates.io` dependencies (`smoltcp`, `webpki-roots`).

**Manual path — the individual component build chain**

```sh
make -C CactLibc-x86_32              # libc (libc.a / libc.so / start.o)
make -C Cactsole-x86_32 CACTLIB="../CactLibc-x86_32"
make -C Cgoct-x86_32     CACTLIB="../CactLibc-x86_32"
make -C CactUserBins-x86_32 install  # fills LocalRepo lib/bin, lib/sbin
make -C LocalRepoCactOS-x86_32       # packs cctkfs.img (drivers + userland)
make -C CactKernel-x86_32            # kernel.bin
./build.sh --build                   # or assemble the ISO via grub-mkrescue
```

**Standalone `build.py`**

```sh
python3 build.py                # auto-detects kernel.bin + cctkfs.img
python3 build.py --help         # show available flags
python3 build.py --non-gui-iso  # non-GUI ISO
python3 build.py --gui-iso      # GUI ISO
python3 build.py --no-deps      # skip rebuild, repack only
```

`build.py` resolves sibling repositories by their current `-x86_32` names
(`LocalRepoCactOS-x86_32`, `CactLibc-x86_32`, `*-for-Cact-x86_32`) with the
legacy names as fallbacks, auto-**clones** any missing repo from
`https://github.com/QwaYer/<repo>`, and installs the toolchain (system packages
via pacman/apt/dnf + rust `nightly` + `rust-src`) when absent — so it works on a
fresh machine. Provision only the toolchain and clones with `--deps`.

Optional extra userland (the `tcc` compiler and `nano`) is skipped unless you
set `CACT_BUILD_EXTRAS=1` (it isn't required for a bootable ISO).

Overrides via `config/local.mk.py` (see `config/local.mk.example`).

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
