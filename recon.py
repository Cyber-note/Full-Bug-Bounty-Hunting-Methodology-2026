#!/usr/bin/env python3
"""Run a small, authorized recon workflow on Windows or Linux."""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


DOMAIN_RE = re.compile(
    r"(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"[A-Za-z]{2,63}\Z"
)


def run(command, *, input_file=None, output_file=None):
    source = input_file.open(encoding="utf-8") if input_file else None
    try:
        with output_file.open("w", encoding="utf-8") if output_file else open(os.devnull, "w") as sink:
            result = subprocess.run(
                command, stdin=source, stdout=sink, check=False
            )
    finally:
        if source:
            source.close()
    if result.returncode:
        raise RuntimeError(f"{command[0]} failed with exit code {result.returncode}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("domain", nargs="?", help="in-scope domain, e.g. example.com")
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--check", action="store_true", help="check runtime and required tools")
    args = parser.parse_args()

    if args.domain and not DOMAIN_RE.fullmatch(args.domain):
        parser.error("domain must be a valid DNS name such as example.com")

    tools = ("subfinder", "dnsx", "httpx")
    if args.check:
        print(f"Python: {sys.version.split()[0]} {'OK' if sys.version_info >= (3, 9) else 'too old (need 3.9+)'}")
        missing = []
        for tool in tools:
            found = shutil.which(tool)
            print(f"{tool}: {found or 'MISSING'}")
            if not found:
                missing.append(tool)
        if missing:
            print("\nInstall missing tools:")
            print("  Linux: install Go, then run:")
            print("    go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest")
            print("    go install github.com/projectdiscovery/dnsx/cmd/dnsx@latest")
            print("    go install github.com/projectdiscovery/httpx/cmd/httpx@latest")
            print("  Windows: install Go (https://go.dev/dl/), then run the same commands in PowerShell.")
            print("  Add Go's bin directory to PATH (Linux: ~/go/bin; Windows: %USERPROFILE%\\go\\bin).")
            return 1
        print("All prerequisites are available.")
        return 0

    if not args.domain:
        parser.error("domain is required unless using --check")

    output = args.output or Path.cwd() / f"recon-{args.domain}"
    output.mkdir(parents=True, exist_ok=True)
    output = output.resolve()
    missing = [tool for tool in tools if shutil.which(tool) is None]
    if missing:
        parser.error("missing required PATH tools: " + ", ".join(missing) + "; run with --check for setup instructions")

    print(f"Authorized recon for {args.domain}; verify it is in scope.")
    subs = output / "subdomains.txt"
    resolved = output / "resolved.txt"
    alive = output / "alive.txt"
    print("[1/3] Passive subdomain enumeration...")
    run(["subfinder", "-d", args.domain, "-silent", "-o", str(subs)])
    print("[2/3] DNS resolution...")
    run(["dnsx", "-silent", "-o", str(resolved)], input_file=subs)
    print("[3/3] HTTP probing...")
    run(
        ["httpx", "-silent", "-status-code", "-title", "-tech-detect", "-o", str(alive)],
        input_file=resolved,
    )
    print(f"Recon complete. Results: {output}")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
