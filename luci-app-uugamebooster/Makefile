include $(TOPDIR)/rules.mk

PKG_NAME:=luci-app-uugamebooster
PKG_VERSION:=2.5
PKG_RELEASE:=2
UPSTREAM_COMMIT:=4984a88b92a07212dc047094eef59a7c9a45b9f1
PKG_SOURCE:=uu-gamebooster-$(UPSTREAM_COMMIT).tar.gz
PKG_SOURCE_URL:=https://codeload.github.com/xiaodoudou/luci-app-uugamebooster/tar.gz
PKG_SOURCE_URL_FILE:=$(UPSTREAM_COMMIT)
PKG_HASH:=54cceecc026e29719617d29bd3ce21cd84a8ac04e3052cc7766651460313a691
PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(UPSTREAM_COMMIT)

ZIG_VERSION:=0.13.0
ZIG_ARCHIVE:=zig-linux-x86_64-$(ZIG_VERSION).tar.xz

# Zig strips both shared objects at link time. The SDK strip tool only handles x86.
RSTRIP:=:
include $(INCLUDE_DIR)/package.mk

# Set after package.mk, which supplies the default unpack command.
PKG_UNPACK:=$(TAR) -xzf "$(DL_DIR)/$(PKG_SOURCE)" -C "$(PKG_BUILD_DIR)" --strip-components=1

define Download/zig
  FILE:=$(ZIG_ARCHIVE)
  URL:=https://ziglang.org/download/$(ZIG_VERSION)
  HASH:=d45312e61ebcc48032b77bc4cf7fd6915c11fa16e4aad116b66c9468211230ea
endef
$(eval $(call Download,zig))

define Package/luci-app-uugamebooster
  SECTION:=luci
  CATEGORY:=LuCI
  SUBMENU:=3. Applications
  TITLE:=LuCI support for NetEase UU Game Booster
  URL:=https://github.com/xiaodoudou/luci-app-uugamebooster
  DEPENDS:=@TARGET_x86_64 +luci-base +luci-compat +luci-lua-runtime +kmod-tun +libstdcpp \
    +kmod-ipt-nat +ca-bundle +unshare +ip-tiny +nftables +iptables-nft +tcpdump-mini +curl
endef

define Package/luci-app-uugamebooster/conffiles
/etc/config/uuplugin
endef

define Build/Prepare
	$(call Build/Prepare/Default)
	mkdir -p "$(PKG_BUILD_DIR)/zig"
	$(TAR) -xJf "$(DL_DIR)/$(ZIG_ARCHIVE)" -C "$(PKG_BUILD_DIR)/zig" --strip-components=1
	python3 ./prepare-runtime.py "$(PKG_BUILD_DIR)/$(PKG_NAME)/root/etc/init.d/uuplugin"
endef

define Build/Configure
endef

define Build/Compile
	mkdir -p "$(PKG_BUILD_DIR)/runtime"
	ZIG_GLOBAL_CACHE_DIR="$(PKG_BUILD_DIR)/zig-cache" "$(PKG_BUILD_DIR)/zig/zig" cc \
		-target x86_64-linux-musl -shared -fPIC -O2 -s \
		-o "$(PKG_BUILD_DIR)/runtime/uu-view-preload-x86_64.so" "$(PKG_BUILD_DIR)/src/uu-view-preload.c"
	ZIG_GLOBAL_CACHE_DIR="$(PKG_BUILD_DIR)/zig-cache" "$(PKG_BUILD_DIR)/zig/zig" cc \
		-target aarch64-linux-musl -shared -fPIC -O2 -s \
		-o "$(PKG_BUILD_DIR)/runtime/uu-view-preload-aarch64.so" "$(PKG_BUILD_DIR)/src/uu-view-preload.c"
	python3 "$(PKG_BUILD_DIR)/tools/po2lmo.py" \
		"$(PKG_BUILD_DIR)/$(PKG_NAME)/po/zh_Hans/uugamebooster.po" \
		"$(PKG_BUILD_DIR)/runtime/uugamebooster.zh-cn.lmo"
endef

define Package/luci-app-uugamebooster/install
	$(INSTALL_DIR) $(1)/usr/lib/lua/luci/i18n $(1)/usr/lib/uuplugin
	$(CP) "$(PKG_BUILD_DIR)/$(PKG_NAME)/luasrc/." $(1)/usr/lib/lua/luci/
	$(CP) "$(PKG_BUILD_DIR)/$(PKG_NAME)/root/." $(1)/
	$(INSTALL_DATA) "$(PKG_BUILD_DIR)/runtime/"*.so $(1)/usr/lib/uuplugin/
	$(INSTALL_DATA) "$(PKG_BUILD_DIR)/runtime/"*.lmo $(1)/usr/lib/lua/luci/i18n/
	chmod 0755 $(1)/etc/init.d/uuplugin $(1)/etc/uci-defaults/45_luci-uuplugin
	chmod 0755 $(1)/usr/libexec/uuplugin/uu-* $(1)/usr/libexec/uuplugin/xt/iptables
endef

$(eval $(call BuildPackage,luci-app-uugamebooster))
