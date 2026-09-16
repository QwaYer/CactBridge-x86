#!/usr/bin/env python3
"""CactBridge — self-provisioning CactOS ISO builder.

Resolves the sibling repositories under the *parent* of this directory
(~/Projects by default), auto-cloning any that are missing from GitHub, ensures
the toolchain is present (system packages + rust nightly + rust-src), then
builds the kernel + cctkfs image and assembles a bootable ISO with
grub-mkrescue.

This script works on a fresh machine: missing sibling repositories are cloned
from <GITHUB> and missing build tools are installed via the detected package
manager (pacman / apt / dnf) together with a rust nightly toolchain.
"""
import argparse
import multiprocessing
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(ROOT, ".."))
JOBS = int(os.environ.get("JOBS", multiprocessing.cpu_count()))
GITHUB = "https://github.com/QwaYer"

# Preferred (current "-x86_32") names first, legacy names as fallbacks.
REPO_CANDIDATES = {
    "kernel": ["CactKernel-x86_32"],
    "libc": ["CactLibc-x86_32", "CactLib-x86_32"],
    "sole": ["Cactsole-x86_32"],
    "cgoct": ["Cgoct-x86_32"],
    "cgoct_gui": ["Cgoct-gui-x86_32"],
    "xfbdev": ["CactXfbdev-x86_32"],
    "userbins": ["CactUserBins-x86_32"],
    "localrepo": ["LocalRepoCactOS-x86_32", "LocalRepoCactOS", "LocalRepoCactOS-non-gui"],
    "localrepo_gui": ["LocalRepoCactOS-gui"],
}

# Driver module repos: installed into the LocalRepo lib/ as *.cctk.
DRIVERS = ["AHCI", "NVMe", "Virtio-net", "Yukon", "Intel-HDA"]

REQUIRED_TOOLS = ["gcc", "clang", "make", "meson", "ninja", "ar", "git", "nasm",
                  "grub-mkrescue", "xorriso", "mformat", "python3", "rustup"]

PACMAN_PKGS = {
    "gcc": "gcc",
    "clang": "clang",
    "meson": "meson",
    "ninja": "ninja",
    "make": "base-devel",
    "ar": "binutils",
    "git": "git",
    "nasm": "nasm",
    "grub-mkrescue": "grub",
    "xorriso": "xorriso",
    "mformat": "mtools",
    "python3": "python",
    "rustup": "rustup",
    "cargo": "rustup",
    "rustc": "rustup",
}
APT_PKGS = {
    "gcc": "gcc",
    "clang": "clang",
    "meson": "meson",
    "ninja": "ninja",
    "make": "make",
    "ar": "binutils",
    "git": "git",
    "nasm": "nasm",
    "grub-mkrescue": "grub-pc-bin",
    "xorriso": "xorriso",
    "mformat": "mtools",
    "python3": "python3",
    "rustup": "rustup",
}
DNF_PKGS = {
    "gcc": "gcc",
    "clang": "clang",
    "meson": "meson",
    "ninja": "ninja",
    "make": "make",
    "ar": "binutils",
    "git": "git",
    "nasm": "nasm",
    "grub-mkrescue": "grub2-tools",
    "xorriso": "xorriso",
    "mformat": "mtools",
    "python3": "python3",
    "rustup": "rustup",
}


class Config:
    def __init__(self):
        self.KERNEL_BIN = os.path.join(SRC, "CactKernel-x86_32", "build-meson", "kernel.bin")
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
    allowed = {"Config": Config, "config": config, "os": os,
               "abspath": os.path.abspath, "join": os.path.join}
    with open(path) as f:
        exec(f.read(), {"__builtins__": {}}, allowed)


def tool_ok(cmd):
    return shutil.which(cmd) is not None


def _sudo_prefix():
    if os.geteuid() == 0:
        return []
    return ["sudo"] if tool_ok("sudo") else []


def _detect_pkgs():
    if tool_ok("pacman"):
        return ("pacman", PACMAN_PKGS)
    if tool_ok("apt-get"):
        return ("apt", APT_PKGS)
    if tool_ok("dnf"):
        return ("dnf", DNF_PKGS)
    return (None, {})


def ensure_system():
    pm, pkgs_map = _detect_pkgs()
    missing = sorted({pkg for tool, pkg in pkgs_map.items() if not tool_ok(tool)})
    if pm and missing:
        print("==> installing missing system packages:", " ".join(missing))
        try:
            if pm == "pacman":
                subprocess.check_call(_sudo_prefix() + ["pacman", "-S", "--needed",
                                                        "--noconfirm"] + missing)
            elif pm == "apt":
                subprocess.check_call(_sudo_prefix() + ["apt-get", "update", "-y"])
                subprocess.check_call(_sudo_prefix() + ["apt-get", "install", "-y"] + missing)
            elif pm == "dnf":
                subprocess.check_call(_sudo_prefix() + ["dnf", "install", "-y"] + missing)
        except subprocess.CalledProcessError as e:
            print(f"WARNING: failed to install packages: {e}", file=sys.stderr)
    if pm is None:
        gone = [t for t in REQUIRED_TOOLS if not tool_ok(t)]
        if gone:
            raise RuntimeError(
                f"unsupported package manager; manually install: {', '.join(gone)}")
    gone = [t for t in REQUIRED_TOOLS if not tool_ok(t)]
    if gone:
        raise RuntimeError(
            "missing required build tools (failed to install): " + ", ".join(gone))


def ensure_rust():
    cargo_bin = os.path.expanduser("~/.cargo/bin")
    os.environ["PATH"] = cargo_bin + os.pathsep + os.environ.get("PATH", "")
    if not tool_ok("rustup"):
        raise RuntimeError("rustup not found — install it, then re-run build.py")
    if not tool_ok("cargo") or not tool_ok("rustc"):
        subprocess.check_call(["rustup", "default", "nightly"])
    if subprocess.run(["rustup", "toolchain", "list"], capture_output=True,
                      text=True).stdout.count("nightly") == 0:
        subprocess.check_call(["rustup", "toolchain", "install", "nightly",
                               "--profile", "minimal"])
    comp = subprocess.run(["rustup", "component", "list", "--toolchain", "nightly"],
                          capture_output=True, text=True).stdout
    src_installed = any("rust-src" in ln and "installed" in ln
                        for ln in comp.splitlines())
    if not src_installed:
        subprocess.check_call(["rustup", "component", "add", "rust-src",
                               "--toolchain", "nightly"])
    print("==> rust", subprocess.run(["rustc", "+nightly", "--version"],
                                     capture_output=True, text=True).stdout.strip())


def bootstrap():
    ensure_system()
    ensure_rust()


def _git(probe=False, timeout=20):
    if probe:
        return ["timeout", str(timeout), "git", "ls-remote", "--exit-code"]
    return ["timeout", str(timeout), "git"]


def git_repo_exists(url):
    r = subprocess.run(_git(probe=True) + [url, "HEAD"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return r.returncode == 0


def resolve(key, required=True):
    """Return the first existing candidate dir, else clone it from GitHub.

    If no candidate can be found or cloned, return None when the project is
    optional, or exit with an error when it is required.
    """
    for name in REPO_CANDIDATES[key]:
        d = os.path.join(SRC, name)
        if os.path.isdir(d):
            return d
        url = f"{GITHUB}/{name}.git"
        if git_repo_exists(url):
            print(f"  cloning {name} ...")
            subprocess.check_call(_git(probe=False, timeout=300) +
                                  ["clone", "--depth", "1", url, d],
                                  stdout=subprocess.DEVNULL)
            return d
    if required:
        print(f"ERROR: required project '{key}' not found and not downloadable:\n"
              f"       tried: {', '.join(REPO_CANDIDATES[key])}", file=sys.stderr)
        sys.exit(1)
    return None


def driver_dir(name):
    for candidate in [f"{name}-for-Cact-x86_32", f"{name}-for-Cact"]:
        d = os.path.join(SRC, candidate)
        if os.path.isdir(d):
            return d
        url = f"{GITHUB}/{candidate}.git"
        if git_repo_exists(url):
            print(f"  cloning {candidate} ...")
            subprocess.check_call(_git(probe=False, timeout=300) +
                                  ["clone", "--depth", "1", url, d],
                                  stdout=subprocess.DEVNULL)
            return d
    return None


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


def run_ninja(target=None, cwd=None, setup_cross=None, opts=None):
    """Build a Meson/Ninja project, configuring build-meson/ on first use."""
    name = os.path.basename(cwd or ".")
    print(f"  {name}...")
    build_dir = os.path.join(cwd or ".", "build-meson")
    opt_args = [f"-D{k}={v}" for k, v in (opts or {}).items()]
    if not os.path.isfile(os.path.join(build_dir, "build.ninja")):
        cmd = ["meson", "setup", build_dir]
        if setup_cross:
            cmd += ["--cross-file", setup_cross]
        subprocess.check_call(cmd + opt_args, cwd=cwd)
    elif opt_args:
        subprocess.check_call(["meson", "configure", build_dir] + opt_args, cwd=cwd)
    cmd = ["ninja", "-C", build_dir]
    if target:
        cmd.append(target)
    subprocess.check_call(cmd)


def build_deps(variant):
    kern = resolve("kernel")
    libc = resolve("libc")
    sole = resolve("sole")
    cgoct = resolve("cgoct")
    userbins = resolve("userbins")
    repo = resolve("localrepo_gui" if variant == "gui" else "localrepo")
    repo_dir = repo
    libc_opts = {"CACTLIB": libc}
    # Meson spellings of the same paths (libc publishes under build-meson/).
    libc_meson_opts = {"cactlib": libc}

    print("Building dependencies...")
    run_ninja(cwd=libc, setup_cross="cross/i686-cact-clang.ini")

    run_ninja(cwd=sole, setup_cross="cross/i686-cact-clang.ini",
              opts=libc_meson_opts)
    run_ninja(cwd=cgoct, setup_cross="cross/i686-cact-clang.ini",
              opts=libc_meson_opts)

    for _d in ["lib/bin", "lib/sbin"]:
        _p = os.path.join(repo_dir, _d)
        if os.path.isdir(_p):
            shutil.rmtree(_p)

    if variant == "gui":
        cgoct_gui = resolve("cgoct_gui")
        xfbdev = resolve("xfbdev")
        run_make(cwd=cgoct_gui, opts=libc_opts)
        run_make(cwd=xfbdev, opts=libc_opts)
        for d in DRIVERS:
            drv = driver_dir(d)
            if drv:
                run_ninja("stage", cwd=drv,
                          setup_cross="cross/i686-cact-clang.ini",
                          opts={"kern_root": kern, "local_repo": repo_dir})
        run_make(cwd=repo_dir, opts={
            "CACTLIB_DIR": libc,
            "XFBDEV_BIN": os.path.join(xfbdev, "build", "xfbdev"),
            "CGOCT_GUI_BIN": os.path.join(cgoct_gui, "cgoct-gui"),
            "USERBINS_MK": userbins,
            "LR_BIN": os.path.join(repo_dir, "lib", "bin"),
            "LR_SBIN": os.path.join(repo_dir, "lib", "sbin"),
        })
    else:
        run_ninja("stage", cwd=userbins,
                  setup_cross="cross/i686-cact-clang.ini",
                  opts={"cactlib": libc,
                        "cactsoleinc": os.path.join(sole, "include"),
                        "lr_bin": os.path.join(repo_dir, "lib", "bin"),
                        "lr_sbin": os.path.join(repo_dir, "lib", "sbin")})
        for d in DRIVERS:
            drv = driver_dir(d)
            if drv:
                run_ninja("stage", cwd=drv,
                          setup_cross="cross/i686-cact-clang.ini",
                          opts={"kern_root": kern, "local_repo": repo_dir})
        run_ninja("stage", cwd=repo_dir,
                  opts={"cactlib_dir": libc,
                        "cactsole_bin": os.path.join(sole, "build-meson", "cactsole"),
                        "cgoct_bin": os.path.join(cgoct, "build-meson", "cgoct"),
                        "userbins_mk": userbins,
                        "cactsoleinc": os.path.join(sole, "include")})
    run_ninja("kernel.bin", cwd=kern, setup_cross="cross/i686-cact-clang.ini")


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
    "CactKernel-x86_32", "CactLibc-x86_32", "CactLib-x86_32",
    "Cactsole-x86_32", "Cgoct-x86_32", "Cgoct-gui-x86_32",
    "CactUserBins-x86_32", "CactXfbdev-x86_32",
    "LocalRepoCactOS-x86_32", "LocalRepoCactOS", "LocalRepoCactOS-gui",
    "LocalRepoCactOS-non-gui",
    "AHCI-for-Cact-x86_32", "NVMe-for-Cact-x86_32",
    "Virtio-net-for-Cact-x86_32", "Yukon-for-Cact-x86_32",
    "Intel-HDA-for-Cact-x86_32",
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


QEMU_PKG = {"qemu-system-i386": "qemu-system-x86"}


def ensure_qemu():
    if tool_ok("qemu-system-i386"):
        return True
    pm, _pkgs = _detect_pkgs()
    if not pm:
        return False
    pkg = QEMU_PKG["qemu-system-i386"]
    print(f"==> installing {pkg} (needed for --run) ...")
    try:
        if pm == "pacman":
            subprocess.check_call(_sudo_prefix() + ["pacman", "-S", "--needed",
                                                    "--noconfirm", pkg])
        elif pm == "apt":
            subprocess.check_call(_sudo_prefix() + ["apt-get", "install", "-y", pkg])
        elif pm == "dnf":
            subprocess.check_call(_sudo_prefix() + ["dnf", "install", "-y", pkg])
    except subprocess.CalledProcessError as e:
        print(f"WARNING: could not install {pkg}: {e}", file=sys.stderr)
        return False
    return tool_ok("qemu-system-i386")


def launch_qemu(cfg):
    kern = resolve("kernel")
    if not tool_ok("qemu-system-i386"):
        print("==> qemu-system-i386 missing — attempting install ...")
        if not ensure_qemu():
            print("ERROR: qemu-system-i386 not found.", file=sys.stderr)
            print("       Install it manually, e.g.:  sudo pacman -S --needed qemu-system-x86",
                  file=sys.stderr)
            sys.exit(1)
    env = {**os.environ, "CACT_ISO": cfg.OUT_ISO}
    subprocess.check_call(["/bin/sh", os.path.join(kern, "run_qemu.sh")], env=env)


def main():
    parser = argparse.ArgumentParser(description="CactBridge — CactOS ISO builder")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--gui-iso", action="store_true", help="Build GUI ISO (cgoct-gui + compositor)")
    group.add_argument("--non-gui-iso", action="store_true", help="Build non-GUI ISO (init + shell)")
    parser.add_argument("--clean", action="store_true", help="Clean CactBridge artifacts")
    parser.add_argument("--clean-env", action="store_true", help="Clean all sibling projects")
    parser.add_argument("--local-config", metavar="FILE", help="Python config file with overrides")
    parser.add_argument("--no-deps", action="store_true", help="Skip dependency builds (repack only)")
    parser.add_argument("--deps", action="store_true", help="Install toolchain + clone missing projects and exit")
    parser.add_argument("--run", action="store_true", help="Launch the built ISO in QEMU")

    args = parser.parse_args()

    if not (args.gui_iso or args.non_gui_iso or args.clean or args.clean_env or args.deps):
        parser.error("specify --gui-iso, --non-gui-iso, --deps, --clean, or --clean-env")

    cfg = Config()
    if args.local_config:
        load_local_config(cfg, args.local_config)

    if args.gui_iso:
        cfg.MB2_MODULE_ISO_NAME = "cctkfs.img"
        cfg.OUT_ISO = os.path.join(ROOT, "build", "cact-gui.iso")
    elif args.non_gui_iso:
        cfg.MB2_MODULE_ISO_NAME = "cctkfs.img"
        cfg.MB2_MODULE_CMDLINE = "cctkfs"
        cfg.OUT_ISO = os.path.join(ROOT, "build", "cact-non-gui.iso")

    if args.clean:
        clean(cfg)
    if args.clean_env:
        clean(cfg, env=True)

    if args.deps:
        bootstrap()
        print("==> resolving repositories ...")
        resolve("kernel")
        resolve("libc")
        resolve("sole")
        resolve("cgoct")
        resolve("userbins")
        resolve("localrepo")
        for d in DRIVERS:
            driver_dir(d)
        print("==> dependencies ready")
        return

    if args.gui_iso or args.non_gui_iso:
        variant = "gui" if args.gui_iso else "non-gui"
        if not args.no_deps:
            bootstrap()
            build_deps(variant)
        repo = resolve("localrepo_gui" if variant == "gui" else "localrepo")
        cfg.MB2_MODULE_SRC = os.path.join(repo, "cctkfs.img")
        cfg.KERNEL_BIN = os.path.join(resolve("kernel"), "build-meson", "kernel.bin")
        build_iso(cfg)
        print(f"  -> {cfg.OUT_ISO}")

    if args.run:
        launch_qemu(cfg)


if __name__ == "__main__":
    main()
