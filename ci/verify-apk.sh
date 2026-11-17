#!/usr/bin/env bash
set -euo pipefail

feed=$(cd "$(dirname "$0")/.." && pwd)
build=$(mktemp -d)
trap 'rm -rf -- "$build"' EXIT
cd "$build"

release=${1:-latest}
releases=https://downloads.immortalwrt.org/releases
fetch() {
    curl -fsSL --proto '=https' --proto-redir '=https' --connect-timeout 20 --retry 3 "$@"
}

if [[ "$release" == latest ]]; then
    release=$(fetch "$releases/" |
        grep -oE 'href="25\.12\.[0-9]+/"' |
        cut -d '"' -f 2 | tr -d / | sort -Vu | tail -n 1)
fi
if [[ ! "$release" =~ ^25\.12\.[0-9]+$ ]]; then
    echo "SDK version must be latest or a stable 25.12.x patch release." >&2
    exit 1
fi

base="$releases/$release/targets/x86/64"
fetch "$base/sha256sums" -o sha256sums
entry=$(awk -v prefix="immortalwrt-sdk-$release-x86-64_" '
    { sub(/^\*/, "", $2) }
    index($2, prefix) == 1 && $2 ~ /^[a-zA-Z0-9._-]+\.Linux-x86_64\.tar\.zst$/ {
        print $1, $2
    }
' sha256sums)
read -r checksum sdk <<< "$entry"
if [[ "$entry" == *$'\n'* || ! "$checksum" =~ ^[0-9a-f]{64}$ || -z "$sdk" ]]; then
    echo "Expected one x86/64 Linux SDK in ImmortalWrt $release checksums." >&2
    exit 1
fi
printf 'ImmortalWrt SDK %s (%s)\n' "$release" "$sdk"
fetch "$base/$sdk" -o "$sdk"
printf '%s  %s\n' "$checksum" "$sdk" | sha256sum -c -

mkdir sdk
tar --zstd -xf "$sdk" -C sdk --strip-components=1
rm -- "$sdk"
cd sdk

# Preserve the SDK's pinned official feed revisions.
cp feeds.conf.default feeds.conf
printf '\nsrc-link uugame %s\n' "$feed" >> feeds.conf
./scripts/feeds update base packages luci uugame
./scripts/feeds install -p uugame luci-app-uugamebooster

cat > .config <<'EOF'
# CONFIG_ALL is not set
# CONFIG_ALL_NONSHARED is not set
# CONFIG_ALL_KMODS is not set
CONFIG_PACKAGE_luci-app-uugamebooster=m
EOF
make defconfig 2>&1 | tee "$build/defconfig.log"
if grep -E "luci-app-uugamebooster/Makefile.*dependency.*does not exist" "$build/defconfig.log"; then
    exit 1
fi
grep -Fx 'CONFIG_USE_APK=y' .config
grep -Fx 'CONFIG_PACKAGE_luci-app-uugamebooster=m' .config
make -j"$(nproc)" package/feeds/uugame/luci-app-uugamebooster/compile V=s

mapfile -t packages < <(find bin -type f -name 'luci-app-uugamebooster-*.apk')
[[ ${#packages[@]} -eq 1 ]]
# Resolve packages with the same explicit ip-full requirement as PassWall.
# The previous UU package required ip-tiny and failed at this step in firmware builds.
apk="$PWD/staging_dir/host/bin/apk"
mkdir "$build/repo" "$build/solver"
while IFS= read -r -d '' package; do
    ln -s "$(realpath "$package")" "$build/repo/"
done < <(find bin -type f -name '*.apk' -print0)
"$apk" mkndx --allow-untrusted --output "$build/repo/packages.adb" "$build/repo/"*.apk
"$apk" --root "$build/solver" --arch x86_64 add \
    --allow-untrusted --no-cache --initdb --no-chown --no-scripts --repositories-file /dev/null \
    --repository "file://$build/repo/packages.adb" luci-app-uugamebooster ip-full

stage="$build/apk"
mkdir "$stage"
staging_dir/host/bin/apk extract --allow-untrusted --destination "$stage" "${packages[0]}"
test -x "$stage/etc/init.d/uuplugin"
test -x "$stage/usr/libexec/uuplugin/xt/iptables"
test -s "$stage/etc/config/uuplugin"
test -s "$stage/usr/lib/lua/luci/controller/uuplugin.lua"
test -s "$stage/usr/lib/lua/luci/i18n/uugamebooster.zh-cn.lmo"
readelf -h "$stage/usr/lib/uuplugin/uu-view-preload-x86_64.so" | grep -F 'Advanced Micro Devices X86-64'
readelf -h "$stage/usr/lib/uuplugin/uu-view-preload-aarch64.so" | grep -F 'AArch64'
sh -n "$stage/etc/init.d/uuplugin"
sha256sum "${packages[0]}"
