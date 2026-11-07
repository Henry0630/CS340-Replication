#!/usr/bin/env python3
"""Print the environment block that docs/environment.md and the report need.

Everything the graders ask for (hardware, OS and kernel version, compiler and
tool versions, and settings that affect results) must be pinned; this script is
how we collect it without hand-typing things we cannot verify.

Works on Linux (the target: WSL2 / container / VM) and on Windows (the host).
Standard library only.

Usage:
    python scripts/check_env.py            # print a markdown block
    python scripts/check_env.py --write    # also save results/env-<host>.md
"""

import argparse
import ctypes
import os
import platform
import shutil
import socket
import subprocess
import sys


def run(cmd, timeout=10):
    """Run a version command; Windows tools print in the OEM codepage, so decode
    leniently instead of assuming UTF-8."""
    try:
        out = subprocess.run(cmd, shell=True, capture_output=True, timeout=timeout)
        for raw in (out.stdout, out.stderr):
            if raw and raw.strip():
                txt = raw.decode("utf-8", "replace").strip()
                if "\ufffd" in txt:
                    txt = raw.decode("gbk", "replace").strip()
                return txt.splitlines()[0]
        return None
    except Exception:  # noqa: BLE001 - a missing tool is a normal outcome here
        return None


def total_ram_gb():
    if sys.platform == "win32":
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        return round(stat.ullTotalPhys / 2**30, 1)
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    return round(int(line.split()[1]) / 2**20, 1)
    except OSError:
        pass
    return None


def cpu_model():
    if sys.platform == "win32":
        name = run('powershell -NoProfile -Command "(Get-CimInstance Win32_Processor).Name"', timeout=25)
        if name and "Get-CimInstance" not in name:
            return name
        return os.environ.get("PROCESSOR_IDENTIFIER") or platform.processor()
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor()


def distro():
    try:
        with open("/etc/os-release") as f:
            kv = dict(line.strip().split("=", 1) for line in f if "=" in line)
        return kv.get("PRETTY_NAME", "").strip('"')
    except OSError:
        return platform.platform()


def kernel():
    return run("uname -r") if sys.platform != "win32" else platform.version()


TOOLS = [
    ("Go", "go version"),
    ("Go 编译目标", "go env GOOS GOARCH GOVERSION"),
    ("gcc", "gcc --version"),
    ("git", "git --version"),
    ("python", "python --version"),
    ("docker", "docker --version"),
    ("timeout", "timeout --version"),
    ("nproc / limits", "nproc"),
]

ENV_KEYS = ["GOMAXPROCS", "GOFLAGS", "CGO_ENABLED", "GODEBUG", "GO111MODULE"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--out", default="results")
    args = ap.parse_args()

    cores = os.cpu_count()
    lines = ["| 项 | 值 |", "|---|---|"]
    rows = [
        ("主机名", socket.gethostname()),
        ("平台", platform.platform()),
        ("发行版 / OS", distro()),
        ("内核版本", kernel()),
        ("CPU", "%s（%s 逻辑核）" % (cpu_model(), cores)),
        ("内存", ("%.1f GB" % total_ram_gb()) if total_ram_gb() else "unknown"),
    ]
    for k, v in rows:
        lines.append("| %s | %s |" % (k, v))
    for label, cmd in TOOLS:
        exe = cmd.split()[0]
        val = run(cmd) if shutil.which(exe) else None
        lines.append("| %s | %s |" % (label, val or "（未安装）"))
    for key in ENV_KEYS:
        if os.environ.get(key):
            lines.append("| 环境变量 `%s` | `%s` |" % (key, os.environ[key]))

    notes = []
    if shutil.which("go") is None:
        notes.append("Go 未安装：L2 无法进行（B 的第 2 周阻塞项）")
    if shutil.which("docker") is None:
        notes.append("Docker 未安装：Reproducibility 25% 需要容器镜像或等价物")
    if sys.platform == "win32":
        notes.append("当前在 Windows 主机上运行：L2 的实验必须在 Linux 环境里做（WSL2/容器/VM），"
                     "此表仅用于记录宿主机")
    if notes:
        lines.append("")
        lines.append("**待解决**")
        for n in notes:
            lines.append("- " + n)

    print("\n".join(lines))

    if args.write:
        os.makedirs(args.out, exist_ok=True)
        path = os.path.join(args.out, "env-%s.md" % socket.gethostname())
        with open(path, "w", encoding="utf-8") as f:
            f.write("# 环境快照（%s）\n\n%s\n" % (socket.gethostname(), "\n".join(lines)))
        print("\n(saved to %s)" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
