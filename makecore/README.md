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
| `CactKernel-x86_32` | Kernel | `make -C CactKernel-x86_32` |
| `CactLib-x86_32` | libc | `make -C CactLib-x86_32` |
| `Cactsole-x86_32` | Shell | `make -C Cactsole-x86_32` |
| `Cgoct-x86_32` | Init (PID 1) | `make -C Cgoct-x86_32` |
| `CactUserBins-x86_32` | User utilities | `make -C CactUserBins-x86_32 install` |
| `LocalRepoCactOS` | cctkfs.img packer | `make -C LocalRepoCactOS` |
| `CactBridge` | ISO packer (GRUB) | `make -C CactBridge iso` |
| `AHCI-for-Cact` | AHCI driver | `make -C AHCI-for-Cact install` |
| `NVMe-for-Cact` | NVMe driver | `make -C NVMe-for-Cact install` |
| `Virtio-net-for-Cact` | virtio-net driver | `make -C Virtio-net-for-Cact install` |
| `Yukon-for-Cact` | Yukon NIC driver | `make -C Yukon-for-Cact install` |
| `CactOS-x86_32` | Workspace integrator | `make -C CactOS-x86_32 -j$(nproc)` |

Each component **auto-detects sibling directories** — just run `make` from its directory. Override paths with variables if needed (e.g. `make CACTLIB=/custom/path`).

## 🔧 Full build step by step

```sh
make -C CactOS-x86_32 -j$(nproc)        # full ISO
make -C CactOS-x86_32 -j$(nproc) disk   # ISO + nvme.img
make -C CactOS-x86_32 -j$(nproc) kernel # kernel only
SKIP_DRIVERS=1 make -C CactOS-x86_32    # skip driver rebuild
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
