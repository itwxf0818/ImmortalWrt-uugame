# ImmortalWrt UU 游戏加速器 Feed

为 ImmortalWrt **25.12 x86/64（x86_64，APK）** 提供 `luci-app-uugamebooster`。构建验证使用官方 25.12.2 SDK。适用于自行编译固件或用对应版本的 SDK 生成独立 APK。

## 接入固件编译

将以下一行加入你的 ImmortalWrt 源码根目录下的 `feeds.conf.default`。如果项目已经有 `feeds.conf`，请加到那个生效的文件中。保留现有官方 feeds，尤其是 `packages` 和 `luci`。

```text
src-git uugame https://github.com/itwxf0818/ImmortalWrt-uugame.git;main
```

```sh
./scripts/feeds update -a
./scripts/feeds install -p uugame luci-app-uugamebooster
make menuconfig
```

目标系统选 x86 → x86_64，在 **LuCI → Applications → luci-app-uugamebooster** 选 `y` 随固件打包，或选 `m` 构建独立 APK。保存后运行 `make defconfig`。仅构建插件时可运行：

```sh
make package/feeds/uugame/luci-app-uugamebooster/compile V=s
```

Linux x86_64 构建机需有 Python 3。首次构建会下载固定提交的源代码和固定版 Zig，并核对 SHA-256。

## APK 与运行时

- APK 位于 `bin/packages/x86_64/uugame/`。使用与正在运行的系统匹配的 ImmortalWrt 25.12 SDK 和软件源。尤其是 `kmod-tun`、`kmod-ipt-nat` 必须匹配固件的内核 ABI。SNAPSHOT 请使用同一构建的 SDK 和模块，稳定版 SDK 的测试不能替代 SNAPSHOT 的检查。
- 对自己构建并已核对的未签名 APK，可在相匹配的系统上使用 `apk add --allow-untrusted ./luci-app-uugamebooster-2.5-r2.apk`。普通安装请保留依赖检查。插件依赖由 Makefile 声明，25.12 选用具体的 `iptables-nft` 和 `ip-tiny`，不需要新增第三方依赖 feed。
- 预设为关闭。启用「仅游戏主机」时，PS5 使用网易原生 x86_64 程序。首次启动从网易下载，强制 HTTPS，按网易接口给出的 MD5 核对。该 MD5 来自供应商接口。
- 电脑及手机模式还需要 aarch64 网易程序、QEMU 和兼容库。按上游机制首次使用时下载，QEMU 与兼容库使用固定 SHA-256。本包在构建时生成 x86_64、aarch64 两个设备筛选组件，并包含简体中文 LuCI 翻译。配置保存在 `/etc/config/uuplugin`。

## 上游与验证

来源为 [xiaodoudou/luci-app-uugamebooster](https://github.com/xiaodoudou/luci-app-uugamebooster/tree/4984a88b92a07212dc047094eef59a7c9a45b9f1) 2.5，固定提交和归档校验值见 Makefile。上游 Makefile 标注 Apache 2.0，未找到适用于整个仓库的授权文件。此 feed 提供构建配方，构建时直接从上游获取源码。验证流程只检查本次构建的 APK，构建产物不作为公开发布文件上传。

GitHub Actions 在提交后用官方 SDK 构建并检查 APK 内的关键文件。每周检查上游 `master`，如有变化只在任务摘要列出差异，不合并或执行上游新提交。升级时先审核授权、依赖和下载逻辑，再更新 Makefile 中的提交及 SHA-256，提升包版本并重跑验证。
