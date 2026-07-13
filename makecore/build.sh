#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JOBS="${JOBS:-$(nproc 2>/dev/null || echo 4)}"

usage() {
    echo "Usage: build.sh [--gui-iso | --non-gui-iso] [--clean] [--clean-env] [--run] [--gdb] [--no-deps] [--local-config FILE]"
    exit 1
}

version() {
    local kern_ver="$(cat "$ROOT/CactKernel-x86_32/VERSION" 2>/dev/null || echo "?")"
    local kern_hash="$(cd "$ROOT/CactKernel-x86_32" && git rev-parse --short HEAD 2>/dev/null || echo "?")"
    local bridge_hash="$(cd "$ROOT/CactBridge" && git rev-parse --short HEAD 2>/dev/null || echo "?")"
    echo "CactOS $kern_ver"
    echo "  kernel  $kern_hash"
    echo "  bridge  $bridge_hash"
    echo "  build   $(date '+%Y-%m-%d %H:%M')"
    echo "  jobs    $JOBS"
}

RUN_QEMU=0
QEMU_GDB=0
SHOW_VER=0
BUILD_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --run|-r) RUN_QEMU=1 ;;
        --gdb) QEMU_GDB=1; RUN_QEMU=1 ;;
        --version|-v) SHOW_VER=1 ;;
        --gui-iso|--non-gui-iso|--clean|--clean-env|--no-deps) BUILD_ARGS+=("$1") ;;
        --local-config) BUILD_ARGS+=("$1" "$2"); shift ;;
        -h|--help) python3 "$ROOT/CactBridge/build.py" --help; exit 0 ;;
        *) usage ;;
    esac
    shift
done

if [[ "$SHOW_VER" == "1" ]] && [[ ${#BUILD_ARGS[@]} -eq 0 ]]; then
    version
    exit 0
fi

if [[ ${#BUILD_ARGS[@]} -eq 0 ]]; then
    usage
fi

cd "$ROOT"
version
python3 CactBridge/build.py "${BUILD_ARGS[@]}"

if [[ "$RUN_QEMU" == "1" ]]; then
    ISO=""
    for a in "${BUILD_ARGS[@]}"; do
        case "$a" in
            --gui-iso) ISO="$ROOT/CactBridge/build/cact-gui.iso" ;;
            --non-gui-iso) ISO="$ROOT/CactBridge/build/cact-non-gui.iso" ;;
        esac
    done
    if [[ -z "$ISO" ]]; then
        echo "ERROR: --run requires --gui-iso or --non-gui-iso" >&2
        exit 1
    fi
    if [[ ! -f "$ROOT/CactKernel-x86_32/build/nvme.img" ]]; then
        echo "  creating disk image..."
        "$ROOT/CactKernel-x86_32/build_disk.sh"
    fi
    echo "  launching QEMU..."
    if [[ "$QEMU_GDB" == "1" ]]; then
        echo "  GDB: target remote :1234 (QEMU waiting for connect)"
        QEMU_GDB=1 CACT_ISO="$ISO" "$ROOT/CactKernel-x86_32/run_qemu.sh"
    else
        CACT_ISO="$ISO" "$ROOT/CactKernel-x86_32/run_qemu.sh"
    fi
fi
