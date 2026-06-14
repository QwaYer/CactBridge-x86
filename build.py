#!/usr/bin/env python3
import argparse
import multiprocessing
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(ROOT, ".."))
JOBS = int(os.environ.get("JOBS", multiprocessing.cpu_count()))


class Config:
    def __init__(self):
        self.KERNEL_BIN = os.path.join(SRC, "CactKernel-x86_32", "build", "kernel.bin")
        self.OUT_ISO = os.path.join(ROOT, "build", "cact.iso")
        self.STAGING_ROOT = os.path.join(ROOT, "build", "isodir")
        self.MB2_MODULE_SRC = ""
        self.MB2_MODULE_ISO_NAME = "payload.bin"
        self.MB2_MODULE_CMDLINE = "cctkfs"
        self.GRUB_WITH_MB2 = os.path.join(ROOT, "grub", "menu-with-mb2.cfg")
        self.GRUB_KERNEL_ONLY = os.path.join(ROOT, "grub", "menu-kernel-only.cfg")


def load_local_config(config, path):
    if not os.path.isfile(path):
        print(f"ERROR: local config not found: {path}", file=sys.stderr)
        sys.exit(1)
    allowed = {"Config": Config, "config": config, "os": os, "abspath": os.path.abspath, "join": os.path.join}
    with open(path) as f:
        exec(f.read(), {"__builtins__": {}}, allowed)


def copy_headers(repo_dir):
    src = os.path.join(SRC, "LocalRepoCactOS", "lib")
    for name in ["include", "tcc", "sys"]:
        d = os.path.join(src, name)
        if os.path.isdir(d):
            dst = os.path.join(repo_dir, "lib", name)
            os.makedirs(dst, exist_ok=True)
            for f in os.listdir(d):
                fp = os.path.join(d, f)
                if os.path.isfile(fp):
                    shutil.copy2(fp, os.path.join(dst, f))


def run_make(target=None, opts=None, cwd=None, silent=True):
    name = os.path.basename(cwd or ".")
    print(f"  {name}...")
    cmd = ["make"]
    if silent:
        cmd.append("-s")
    cmd.extend(["-C", cwd or "."])
    cmd.extend(["-j", str(JOBS)])
    if target:
        cmd.append(target)
    if opts:
        for k, v in opts.items():
            cmd.append(f"{k}={v}")
    subprocess.check_call(cmd)


def build_tcc(repo_dir):
    script = os.path.join(SRC, "tinycc-for-CactOS", "build_cactos.sh")
    out = os.path.join(SRC, "tinycc-for-CactOS", "cactos-build", "tcc")
    if not os.path.isfile(out):
        subprocess.check_call(["/bin/sh", script],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    dst = os.path.join(repo_dir, "lib", "bin", "tcc")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(out, dst)


def build_deps(variant):
    lib_dir = os.path.join(SRC, "CactLib-x86_32")
    sole_dir = os.path.join(SRC, "Cactsole-x86_32")
    cgoct_dir = os.path.join(SRC, "Cgoct-x86_32")
    cgoct_gui_dir = os.path.join(SRC, "Cgoct-gui-x86_32")
    userbins_dir = os.path.join(SRC, "CactUserBins-x86_32")
    xfbdev_dir = os.path.join(SRC, "CactXfbdev-x86_32")
    kern_dir = os.path.join(SRC, "CactKernel-x86_32")
    tcc_dir = os.path.join(SRC, "tinycc-for-CactOS")
    drivers = ["AHCI", "NVMe", "Virtio-net", "Yukon"]

    libc_opts = {"CACTLIB": lib_dir}

    print("Building dependencies...")
    run_make(cwd=lib_dir)

    if variant == "gui":
        repo_dir = os.path.join(SRC, "LocalRepoCactOS-gui")
        for _d in ["lib/bin", "lib/sbin"]:
            _p = os.path.join(repo_dir, _d)
            if os.path.isdir(_p):
                shutil.rmtree(_p)
        copy_headers(repo_dir)
        build_tcc(repo_dir)

        run_make(cwd=cgoct_gui_dir, opts=libc_opts)
        run_make(cwd=xfbdev_dir, opts=libc_opts)

        for d in drivers:
            drv_dir = os.path.join(SRC, f"{d}-for-Cact")
            if os.path.isdir(drv_dir):
                run_make("install", {"KERN_ROOT": kern_dir, "LOCAL_REPO": repo_dir}, drv_dir)

        run_make(cwd=repo_dir, opts={
            "CACTLIB_DIR": lib_dir,
            "XFBDEV_BIN": os.path.join(xfbdev_dir, "build", "xfbdev"),
            "CGOCT_GUI_BIN": os.path.join(cgoct_gui_dir, "cgoct-gui"),
            "USERBINS_MK": userbins_dir,
            "LR_BIN": os.path.join(repo_dir, "lib", "bin"),
            "LR_SBIN": os.path.join(repo_dir, "lib", "sbin"),
        })

    else:
        repo_dir = os.path.join(SRC, "LocalRepoCactOS-non-gui")
        for _d in ["lib/bin", "lib/sbin"]:
            _p = os.path.join(repo_dir, _d)
            if os.path.isdir(_p):
                shutil.rmtree(_p)
        copy_headers(repo_dir)
        build_tcc(repo_dir)

        run_make(cwd=sole_dir, opts=libc_opts)
        run_make(cwd=cgoct_dir, opts=libc_opts)
        run_make("install", {
            "CACTLIB": lib_dir,
            "CACTSOLEINC": os.path.join(sole_dir, "include"),
            "LR_BIN": os.path.join(repo_dir, "lib", "bin"),
            "LR_SBIN": os.path.join(repo_dir, "lib", "sbin"),
        }, userbins_dir)

        for d in drivers:
            drv_dir = os.path.join(SRC, f"{d}-for-Cact")
            if os.path.isdir(drv_dir):
                run_make("install", {"KERN_ROOT": kern_dir, "LOCAL_REPO": repo_dir}, drv_dir)

        run_make(cwd=repo_dir, opts={
            "CACTLIB_DIR": lib_dir,
            "CACTSOLE_BIN": os.path.join(sole_dir, "cactsole"),
            "USERBINS_MK": userbins_dir,
            "CACTSOLEINC": os.path.join(sole_dir, "include"),
            "LR_BIN": os.path.join(repo_dir, "lib", "bin"),
            "LR_SBIN": os.path.join(repo_dir, "lib", "sbin"),
        })
        cgoct_bin = os.path.join(cgoct_dir, "cgoct")
        shutil.copy2(cgoct_bin, os.path.join(repo_dir, "lib", "bin", "init"))
        shutil.copy2(cgoct_bin, os.path.join(repo_dir, "lib", "bin", "cgoct"))
        etc_dir = os.path.join(repo_dir, "lib", "etc")
        os.makedirs(etc_dir, exist_ok=True)
        with open(os.path.join(etc_dir, "cgoct.conf"), "w") as f:
            f.write("launch_compositor=0\n")
        packer = os.path.join(repo_dir, "tools", "pack_cctkfs.py")
        subprocess.check_call(["python3", packer, os.path.join(repo_dir, "lib"), os.path.join(repo_dir, "cctkfs-non-gui.img")])

    run_make("build/kernel.bin", cwd=kern_dir)


def build_iso(cfg):
    if not cfg.KERNEL_BIN:
        print("ERROR: KERNEL_BIN is empty", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(cfg.KERNEL_BIN):
        print(f"ERROR: KERNEL_BIN not found: {cfg.KERNEL_BIN}", file=sys.stderr)
        sys.exit(1)

    have_mb2 = bool(cfg.MB2_MODULE_SRC)
    if have_mb2 and not os.path.isfile(cfg.MB2_MODULE_SRC):
        print(f"ERROR: MB2_MODULE_SRC not found: {cfg.MB2_MODULE_SRC}", file=sys.stderr)
        sys.exit(1)

    boot_dir = os.path.join(cfg.STAGING_ROOT, "boot")
    grub_dir = os.path.join(boot_dir, "grub")
    os.makedirs(grub_dir, exist_ok=True)

    shutil.copy2(cfg.KERNEL_BIN, os.path.join(boot_dir, "kernel.bin"))

    if have_mb2:
        shutil.copy2(cfg.MB2_MODULE_SRC, os.path.join(boot_dir, cfg.MB2_MODULE_ISO_NAME))
        with open(cfg.GRUB_WITH_MB2) as f:
            content = f.read()
        content = content.replace("MB2_MODULE_PLACEHOLDER", cfg.MB2_MODULE_ISO_NAME)
        content = content.replace("MB2_CMDLINE_PLACEHOLDER", cfg.MB2_MODULE_CMDLINE)
        with open(os.path.join(grub_dir, "grub.cfg"), "w") as f:
            f.write(content)
    else:
        shutil.copy2(cfg.GRUB_KERNEL_ONLY, os.path.join(grub_dir, "grub.cfg"))

    print(f"  grub-mkrescue  →  {cfg.OUT_ISO}")
    subprocess.check_call(["grub-mkrescue", "-o", cfg.OUT_ISO, cfg.STAGING_ROOT])


ENV_PROJECTS = [
    "CactKernel-x86_32", "CactLib-x86_32", "Cactsole-x86_32",
    "Cgoct-x86_32", "Cgoct-gui-x86_32", "CactUserBins-x86_32",
    "CactXfbdev-x86_32",
    "LocalRepoCactOS", "LocalRepoCactOS-gui", "LocalRepoCactOS-non-gui",
    "AHCI-for-Cact", "NVMe-for-Cact", "Virtio-net-for-Cact", "Yukon-for-Cact",
]


def clean(cfg, env=False):
    if os.path.isdir(cfg.STAGING_ROOT):
        shutil.rmtree(cfg.STAGING_ROOT)
    if os.path.isfile(cfg.OUT_ISO):
        os.remove(cfg.OUT_ISO)
    if env:
        for name in ENV_PROJECTS:
            d = os.path.join(SRC, name)
            mf = os.path.join(d, "Makefile")
            if os.path.isdir(d) and os.path.isfile(mf):
                subprocess.check_call(["make", "-C", d, "clean", "-s"],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"  cleaned  {name}")


def main():
    parser = argparse.ArgumentParser(description="CactBridge — CactOS ISO builder")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--gui-iso", action="store_true", help="Build GUI ISO (cgoct-gui + compositor)")
    group.add_argument("--non-gui-iso", action="store_true", help="Build non-GUI ISO (init + shell)")
    parser.add_argument("--clean", action="store_true", help="Clean CactBridge artifacts")
    parser.add_argument("--clean-env", action="store_true", help="Clean all sibling projects")
    parser.add_argument("--local-config", metavar="FILE", help="Python config file with overrides")
    parser.add_argument("--no-deps", action="store_true", help="Skip dependency builds")

    args = parser.parse_args()

    if not args.gui_iso and not args.non_gui_iso and not args.clean and not args.clean_env:
        parser.error("specify --gui-iso, --non-gui-iso, --clean, or --clean-env")

    cfg = Config()

    if args.local_config:
        load_local_config(cfg, args.local_config)

    if args.gui_iso:
        cfg.MB2_MODULE_SRC = os.path.join(SRC, "LocalRepoCactOS-gui", "cctkfs-gui.img")
        cfg.MB2_MODULE_ISO_NAME = "cctkfs.img"
        cfg.OUT_ISO = os.path.join(ROOT, "build", "cact-gui.iso")
    elif args.non_gui_iso:
        cfg.MB2_MODULE_SRC = os.path.join(SRC, "LocalRepoCactOS-non-gui", "cctkfs-non-gui.img")
        cfg.MB2_MODULE_ISO_NAME = "cctkfs.img"
        cfg.OUT_ISO = os.path.join(ROOT, "build", "cact-non-gui.iso")

    if args.clean:
        clean(cfg)
    if args.clean_env:
        clean(cfg, env=True)

    if args.gui_iso or args.non_gui_iso:
        variant = "gui" if args.gui_iso else "non-gui"
        if not args.no_deps:
            build_deps(variant)
        build_iso(cfg)


if __name__ == "__main__":
    main()
