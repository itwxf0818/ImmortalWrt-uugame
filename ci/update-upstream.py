"""Resolve an upstream commit and apply the same candidate in CI and on publish."""
import hashlib
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

PACKAGE = "luci-app-uugamebooster"
REPO = f"https://github.com/xiaodoudou/{PACKAGE}.git"
MAKEFILE = Path(PACKAGE) / "Makefile"


def field(text, name):
    values = re.findall(rf"^{name}:=([^\n]+)$", text, re.MULTILINE)
    if len(values) != 1:
        raise SystemExit(f"Expected one {name} in Makefile")
    return values[0]


def validate(value, pattern, name):
    if not re.fullmatch(pattern, value):
        raise SystemExit(f"Invalid {name}")


def detect(text, output, summary):
    latest = subprocess.check_output(
        ["git", "ls-remote", "--exit-code", REPO, "refs/heads/master"], text=True
    ).split()[0]
    validate(latest, r"[0-9a-f]{40}", "upstream commit")
    pinned = field(text, "UPSTREAM_COMMIT")
    if latest == pinned:
        output.write("changed=false\n")
        summary.write(f"已是上游最新提交 `{pinned}`。\n")
        return

    with tempfile.TemporaryDirectory() as directory:
        archive = Path(directory) / "source.tar.gz"
        subprocess.run(
            [
                "curl", "-fsSL", "--proto", "=https", "--proto-redir", "=https",
                "--retry", "3", "--max-time", "120", "-o", str(archive),
                f"https://codeload.github.com/xiaodoudou/{PACKAGE}/tar.gz/{latest}",
            ],
            check=True,
        )
        with archive.open("rb") as source:
            checksum = hashlib.file_digest(source, "sha256").hexdigest()
        with tarfile.open(archive) as source:
            member = source.extractfile(f"{PACKAGE}-{latest}/{PACKAGE}/Makefile")
            if member is None:
                raise SystemExit("Missing upstream package Makefile")
            version = field(member.read(65536).decode("utf-8"), "PKG_VERSION")

    validate(version, r"[0-9]+(?:\.[0-9]+)+", "upstream package version")
    summary.write(f"发现上游新提交 `{latest}`（{version}），等待 APK 验证。\n")
    output.write(f"changed=true\ncommit={latest}\nchecksum={checksum}\nversion={version}\n")


def apply(text, commit, checksum, version):
    validate(commit, r"[0-9a-f]{40}", "upstream commit")
    validate(checksum, r"[0-9a-f]{64}", "archive checksum")
    validate(version, r"[0-9]+(?:\.[0-9]+)+", "upstream package version")

    current_version = field(text, "PKG_VERSION")
    if tuple(map(int, version.split("."))) < tuple(map(int, current_version.split("."))):
        raise SystemExit(f"Upstream version decreased from {current_version} to {version}")
    release = int(field(text, "PKG_RELEASE")) + 1
    fields = {
        "UPSTREAM_COMMIT": commit,
        "PKG_HASH": checksum,
        "PKG_VERSION": version,
        "PKG_RELEASE": str(release),
    }
    for name, value in fields.items():
        old = field(text, name)
        text = re.sub(rf"^{name}:={re.escape(old)}$", f"{name}:={value}", text, flags=re.MULTILINE)
    MAKEFILE.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    command, *args = sys.argv[1:]
    text = MAKEFILE.read_text(encoding="utf-8")
    if command == "detect":
        with open(args[0], "a", encoding="utf-8") as output, open(args[1], "a", encoding="utf-8") as summary:
            detect(text, output, summary)
    elif command == "apply":
        apply(text, *args)
    else:
        raise SystemExit(f"Unknown command: {command}")
