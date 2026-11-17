#!/usr/bin/env bash
set -euo pipefail

feed=$(cd "$(dirname "$0")/.." && pwd)
build=$(mktemp -d)
trap 'rm -rf -- "$build"' EXIT
cd "$build"

sdk=immortalwrt-sdk-25.12.2-x86-64_gcc-14.3.0_musl.Linux-x86_64.tar.zst
curl -fsSL --proto '=https' --proto-redir '=https' --retry 3 \
    "https://downloads.immortalwrt.org/releases/25.12.2/targets/x86/64/$sdk" -o "$sdk"
echo "4d4631f134c2f27215a91aa7ef5bf9a01ea96c2450d3b8a5c38048c32462ac60  $sdk" | sha256sum -c -
mkdir sdk
tar --zstd -xf "$sdk" -C sdk --strip-components=1
rm -- "$sdk"
cd sdk

# Preserve the SDK's pinned official feed revisions.
cp feeds.conf.default feeds.conf
printf '\nsrc-link uugame %s\n' "$feed" >> feeds.conf
./scripts/feeds update packages luci uugame
./scripts/feeds install -p uugame luci-app-uugamebooster

cat > .config <<'EOF'
# CONFIG_ALL is not set
# CONFIG_ALL_NONSHARED is not set
# CONFIG_ALL_KMODS is not set
CONFIG_PACKAGE_luci-app-uugamebooster=m
EOF
make defconfig
grep -Fx 'CONFIG_USE_APK=y' .config
grep -Fx 'CONFIG_PACKAGE_luci-app-uugamebooster=m' .config
make -j2 package/feeds/uugame/luci-app-uugamebooster/compile V=s

mapfile -t packages < <(find bin -type f -name 'luci-app-uugamebooster-*.apk')
[[ ${#packages[@]} -eq 1 ]]
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
