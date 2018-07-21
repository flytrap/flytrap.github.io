# 一加6 获取root权限

## 下载相关文件
- twrp: [https://twrp.me/](https://twrp.me/)

TeamWin Recovery Project： 全触屏操作的第三方Recovery, 支持多国语言，很强大

- magisk: [https://github.com/topjohnwu/Magisk/releases/](https://github.com/topjohnwu/Magisk/releases/)
集成 root（MagiskSU）

## 推送文件到手机
``` bash 
gpg --verify twrp-3.2.2-0-enchilada.img.asc twrp-3.2.2-0-enchilada.img  # 引导文件校验
gpg --verify twrp-installer-enchilada-3.2.2-0.zip.asc twrp-installer-enchilada-3.2.2-0.zip  # 安装包校验
adb push twrp-installer-enchilada-3.2.2-0.zip /sdcard/
adb push Magisk-v16.0.zip /sdcard/
```

## 解锁BootLoader
- 此升级方式会清空手机内所有内容，请务必先备份。
- 设置 -> 系统 -> 关于手机 -> 高级 -> 连续点击“版本号”7次打开开发者选项
- 设置 -> 系统 -> 开发者选项 ->  打开“OEM 解锁” -> 打开"高级重启"
- 关机 -> 进入fastboot 

``` bash
adb reboot bootloader  # 进入刷机状态
fastboot oem unlock   # 选择unlock the  bootloader ->确认
```


##  刷入twrp, Magisk包
``` bash
adb reboot bootloader  # 进入到BootLoader
fastboot boot twrp-3.2.2-0-enchilada.img  # 从twrp启动
## 点击install  选择/sdcard/下的zip包安装, 有两个(twrp-installer-enchilada-3.2.2-0.zip)是更改系统recovery， (Magisk-v16.0.zip)是root管理包
adb reboot recovery  # 进入twrp
```
