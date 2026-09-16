# 🌵 CactOS — workspace root

Monolithic OS for **i686**: low-level in **C**, critical subsystems in **Rust**.

## 🚀 Quick Build

```sh
./build-cact-qemu.sh           # full ISO + empty ext4 disk
RUN_QEMU=1 ./build-cact-qemu.sh  # build + launch QEMU
```

## 📦 Components

| Directory | Role | Standalone build |
|---|---|---|
| `CactKernel-x86_32` | Kernel | `ninja -C CactKernel-x86_32/build-meson` |
| `CactLibc-x86_32` | libc | `ninja -C CactLibc-x86_32/build-meson` |
| `Cactsole-x86_32` | Shell | `ninja -C Cactsole-x86_32/build-meson` |
| `Cgoct-x86_32` | Init (PID 1) | `ninja -C Cgoct-x86_32/build-meson` |
| `CactUserBins-x86_32` | User utilities | `ninja -C CactUserBins-x86_32/build-meson stage` |
| `LocalRepoCactOS-x86_32` | cctkfs.img packer | `ninja -C LocalRepoCactOS-x86_32/build-meson stage` |
| `CactBridge-x86` | ISO packer (GRUB) | `python3 CactBridge-x86/build.py --non-gui-iso` |
| `AHCI-for-Cact-x86_32` | AHCI driver | `ninja -C AHCI-for-Cact-x86_32/build-meson stage` |
| `NVMe-for-Cact-x86_32` | NVMe driver | `ninja -C NVMe-for-Cact-x86_32/build-meson stage` |
| `Virtio-net-for-Cact-x86_32` | virtio-net driver | `ninja -C Virtio-net-for-Cact-x86_32/build-meson stage` |
| `Yukon-for-Cact-x86_32` | Yukon NIC driver | `ninja -C Yukon-for-Cact-x86_32/build-meson stage` |
| `CactOS-x86_32` | Workspace integrator | `ninja -C CactOS-x86_32/build-meson stage` |

Every component is its own Meson project and **auto-detects sibling directories** — its `build-meson/` just needs one `meson setup build-meson --cross-file cross/i686-cact-clang.ini` (the integrator targets do that automatically on first use). Override paths with `-D` options, e.g. `meson configure build-meson -Dcactlib=/custom/path`.

## 🔧 Full build step by step

```sh
ninja -C CactOS-x86_32/build-meson stage    # libc → shell → userbins → drivers → cctkfs.img
ninja -C CactOS-x86_32/build-meson kernel   # kernel only
ninja -C CactOS-x86_32/build-meson iso      # full ISO (non-GUI)
ninja -C CactOS-x86_32/build-meson disk     # ISO + nvme.img
ninja -C CactOS-x86_32/build-meson drivers  # out-of-tree modules only
```

## ▶️ Run in QEMU

```sh
CACT_ISO=CactBridge/build/cact.iso CactKernel-x86_32/run_qemu.sh
```

Requires: `qemu-system-i386`, `grub-mkrescue`, `gcc` (i686), `nasm`, `cargo +nightly`.

## 🏗️ Build chain

```
libc → cactsole / cgoct → CactUserBins → drivers → localrepo (cctkfs.img) → kernel → CactBridge (cact.iso)
```

See [CactOS-x86_32/README.md](CactOS-x86_32/README.md) for full tech specs and architecture.
