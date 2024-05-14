---
title: dns 私有服务器
author: flytrap
categories:
  - tech
tags:
  - tech
  - dns
  - 域名解析
  - docker-compose
date: 2024-05-13 14:00:01
---

DNS 服务器是(Domain Name System 或者 Domain Name Service)域名系统或者域名服务,域名系统为 Internet 上的主机分配域名地址和 IP 地址。
公司内部通过域名访问内部服务器，但是域名解析又无法访问到内网， 所以内部 dns 解析服务是最好的解决方案

<!--more-->

## 部署

建议使用 docker 容器化部署，此处给出常用 docker-compose 配置文件

```bash
version: '3'

services:
  bind:
    container_name: dns
    restart: always
    image: sameersbn/bind:9.16.1-20200524
    ports:
    - "53:53/udp" # 绑定容器53端口到宿主机的53端口，DNS默认端口
    - "53:53/tcp"
    - "10000:10000/tcp"  # 图形化界面管理器端口;
    volumes:
    - ./bind:/data   # 挂载本地目录作为dns配置存储
```

```bash
lsof -i:53  # 确认端口占用
```

## ubuntu 端口占用

```bash
sudo systemctl stop systemd-resolved
sudo systemctl disable systemd-resolved
vim /etc/resolv.conf  # 只保留nameserver 一行， 改为127.0.0.1即可
```

## 管理

访问地址: https://localhost:10000
使用 https 访问哦
默认账户和密码 root/password, 进去可以修改

## 调整默认配置

菜单路径如下

```bash
Servers -> BINBIND DNS Server -> Zone Defaults
```

找到: Default zone settings

Allow transfers from: 输入框添加 any, 选项改为 Listed..
Allow queries from: 输入框添加 any, 选项改为 Listed..

保存重启, 不改无法查询公网解析

## 添加自己的正向解析

菜单路径如下

```bash
Servers -> BINBIND DNS Server -> Create Master Zone
```

- Domain name: 写你的名字
- Master server： localhost
- Email address： 看这写

其他默认就好了

返回后 Existing DNS Zones 中选择你刚才添加的名字， 进去选择 Address
输入 Name: 域名, Address: ip ， 点击 Create 就可以了

完了记得重启哦
