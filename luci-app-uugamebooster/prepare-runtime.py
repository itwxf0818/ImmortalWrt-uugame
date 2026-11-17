"""Apply the feed's HTTPS and OEM library verification to the pinned source."""
from pathlib import Path
import sys


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise SystemExit(f"Unexpected upstream download code: {old!r}")
    return source.replace(old, new, 1)


path = Path(sys.argv[1])
source = path.read_text(encoding="utf-8")
source = replace_once(
    source,
    '\tout=$(curl -L -s -k --connect-timeout 10 -H "Accept:text/plain" "$url" 2>/dev/null)\n'
    '\t[ -n "$out" ] || out=$(wget -q --no-check-certificate -O - "$url" 2>/dev/null)\n'
    '\t[ -n "$out" ] || out=$(uclient-fetch -q --no-check-certificate -O - "$url" 2>/dev/null)',
    '\tout=$(curl -fsSL --proto "=https" --proto-redir "=https" --connect-timeout 10 '
    '--max-time 30 -H "Accept:text/plain" "$url") || return 1',
)
start = source.index("fetch_file() {")
end = source.index("download_plugin() {", start)
source = source[:start] + '''fetch_file() {
	local url="$1" dest="$2"
	case "$url" in
		http://*) url="https://${url#http://}" ;;
		https://*) ;;
		*) return 1 ;;
	esac
	curl -fsSL --proto '=https' --proto-redir '=https' --connect-timeout 15 \\
		--max-time 180 "$url" -o "$dest" && [ -s "$dest" ]
}

''' + source[end:]

source = replace_once(source, '\t\t\trm -rf /tmp/oemx && mkdir -p /tmp/oemx', '''
			case "$pkg" in
				libc_1.2.4-4_aarch64_generic.ipk)
					got=b42913a427bca1e697b22d1e353476c4cf4217fca640a40c36a39a2d166f4e05 ;;
				libgcc1_12.3.0-4_aarch64_generic.ipk)
					got=6ac51c299fa75de5964c8b1ac87d476bcfd1d28af2d693c30d1e463baae80a9d ;;
				libstdcpp6_12.3.0-4_aarch64_generic.ipk)
					got=3f174e78dead3941736971da0bd99a2b4dd0b3411bbd6ea4870ae677c49dfef4 ;;
				*) return 1 ;;
			esac
			if ! printf '%s  %s\\n' "$got" "/tmp/$pkg" | sha256sum -c >/dev/null; then
				uu_log "ERROR: OEM library checksum mismatch: $pkg"
				rm -f "/tmp/$pkg"
				return 1
			fi
			rm -rf /tmp/oemx && mkdir -p /tmp/oemx''')
source = replace_once(source, 'if [ ! -e "$OEM_SYSROOT/lib/ld-musl-aarch64.so.1" ]; then',
                      'if [ ! -f "$OEM_SYSROOT/.verified-libs" ]; then')
source = replace_once(source, 'tar xzf "/tmp/$pkg" -C /tmp/oemx 2>/dev/null',
                      'tar xzf "/tmp/$pkg" -C /tmp/oemx 2>/dev/null || return 1')
source = replace_once(source, 'tar xzf /tmp/oemx/data.tar.gz -C "$OEM_SYSROOT" 2>/dev/null',
                      'tar xzf /tmp/oemx/data.tar.gz -C "$OEM_SYSROOT" 2>/dev/null || return 1')
source = replace_once(source, 'ln -sf ld-musl-aarch64.so.1 "$OEM_SYSROOT/lib/libc.so"',
                      'ln -sf ld-musl-aarch64.so.1 "$OEM_SYSROOT/lib/libc.so" || return 1\n'
                      '\t\t: > "$OEM_SYSROOT/.verified-libs" || return 1')

path.write_text(source, encoding="utf-8", newline="\n")
