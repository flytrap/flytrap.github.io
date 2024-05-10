---
title: chrony 时间同步
author: flytrap
categories:
  - tech
tags:
  - tech
  - chrony
  - ntp
  - 时间同步
date: 2024-04-17 10:04:28
---

Chrony 是一个开源自由的网络时间协议 NTP 的客户端和服务器软软件。它能让计算机保持系统时钟与时钟服务器（NTP）同步，因此让你的计算机保持精确的时间，Chrony 也可以作为服务端软件为其他计算机提供时间同步服务。

Chrony 由两个程序组成，分别是 chronyd 和 chronyc

chronyd 是一个后台运行的守护进程，用于调整内核中运行的系统时钟和时钟服务器同步。它确定计算机增减时间的比率，并对此进行补偿。
chronyc 提供了一个用户界面，用于监控性能并进行多样化的配置。它可以在 chronyd 实例控制的计算机上工作，也可以在一台不同的远程计算机上工作。

NTP 是网络时间协议（Network Time Protocol）的简称，通过 udp 123 端口进行网络时钟同步。
RHEL7 中默认使用 chrony 作为时间服务器，也支持 NTP，需要额外安装。
NTP 与 chrony 不能同时存在，只能用其中一个，并将另一个 mask 掉。

<!--more-->

## NTP 协议简介

- NTP(Network Time Protocol，网络时间协议)
- NTP 是用来使网络中的各个计算机时间同步的一种协议
- 可以使用 nepdate 命令来向服务同步时间

## 安装

```bash
sudo apt install chrony -y  # Ubuntu系列
sudo yum install chrony -y  # centos系列
systemctl enable chronyd
systemctl start chronyd
```

## 服务器端

需要添加如下配置

```bash
local stratum 8  # 即使自己未能通过网络时间服务器同步到时间，也允许将本地时间作为标准时间授时给其它客户端
manual
allow 192.168.0.0/16  # 允许使用的网段

timedatectl status  # 查看事件同步状态
timedatectl set-ntp true  # 开启网络事件同步

# System clock synchronized: yes  开启同步
# NTP service: active
```

### 监听的端口

- 123/udp：兼容 ntp 服务监听在 udp 的 123 端口上
- 323/udp：chrony 服务本身监听在 udp 的 323 端口上

## 客户端

```bash
server local.ntp.server iburst

allow 192.168.0.0/16  # 允许使用的网段
```

local.ntp.server 为服务器端地址

## 命令

### chronyc 命令

```bash
chronyc sources -v # 查看连接的时间服务器*是正常状态
chronyc sourcestats -v  # 查看当前时间同步是否正常
chronyc tracking -v  # 校准时间服务器
chronyc activity -v  # ntp servers 是否在线
chronyc -a makestep  # 强制同步系统时刻
```

### timedatectl 命令

```bash
timedatectl list-timezones
timedatectl list-timezones |  grep  -E "Asia/S.*"  # 查看时区

timedatectl set-timezone Asia/Shanghai  # 修改为上海时区
timedatectl set-ntp true/flase  # 是否开启ntp
```

## chronyc sources 输出结果解析

### M

这表示信号源的模式。^表示服务器，=表示对等方，＃表示本地连接的参考时钟。

### S

```bash
* 表示chronyd当前同步到的源。
+ 表示可接受的信号源，与选定的信号源组合在一起。
- 表示被合并算法排除的可接受源。
？ 指示已失去连接性或其数据包未通过所有测试的源。它也显示在启动时，直到从中至少收集了3个样本为止（临时状态）。
x 表示chronyd认为是虚假行情的时钟（即，其时间与大多数其他来源不一致）。
〜 表示时间似乎具有太多可变性的来源。
```

### Name/IP address

这显示了源的名称或 IP 地址，或参考时钟的参考 ID。

### Stratum

这显示了来源的层，如其最近收到的样本中所报告的那样。层 1 表示一台具有本地连接的参考时钟的计算机。与第 1 层计算机同步的计算机位于第 2 层。与第 2 层计算机同步的计算机位于第 3 层，依此类推。

### Poll

这显示轮询源的速率，以秒为单位的时间间隔的以 2 为底的对数。因此，值为 6 表示每 64 秒进行一次测量。**chronyd 会**根据当前情况自动**更改**轮询速率。

### Reach

这显示了源的可达性寄存器以八进制数字打印。寄存器有 8 位，并在每个从源接收或丢失的数据包上更新。值 377 表示从最后八次传输中收到了对所有用户的有效答复。

### LastRx

此列显示多长时间前从来源接收到了最后一个好的样本（在下一列中显示）。未通过某些测试的测量将被忽略。通常以秒为单位。字母*m*，_h_，*d*或*y*表示分钟，小时，天或年。

### Last sample

此列显示上次测量时本地时钟与源之间的偏移。方括号中的数字表示实际测得的偏移量。可以用*ns*（表示纳秒），*us* （表示微秒），_ms_（表示毫秒）或*s*（表示秒）作为后缀。方括号左侧的数字表示原始测量值，已调整为允许此后施加于本地时钟的任何摆度。

*+/-*指示器后面的数字表示测量中的误差范围。正偏移表示本地时钟位于源时钟之前
