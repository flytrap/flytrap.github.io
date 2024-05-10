---
title: SeaFile 网盘
author: flytrap
categories:
  - tech
tags:
  - tech
  - SeaFile
  - docker-compose
  - 网盘
  - 私有网盘
date: 2024-05-11 10:10:00
---

Seafile 是一款开源的企业云盘，注重可靠性和性能，支持全平台客户端。Seafile 内置协同文档 SeaDoc ，让协作撰写、管理和发布文档更便捷。
Seafile 提供全面的网盘功能，用户可以在 Seafile 中存储、管理和共享文件。支持多种文件类型。支持全平台客户端，包括 Windows、Mac、Linux、iOS、Android 多种操作系统以及移动设备，可以在任何设备上轻松访问和管理文件，体验更为统一。
Seafile 的协作功能超越了简单的文件共享。它支持多人协同在线编辑、文档编辑锁定，同时提供权限管理、版本控制和事件通知等功能，使得团队协作更加流畅、可控和高效。

(官网)[https://www.seafile.com/]

<!--more-->

## 部署

建议使用 docker 容器化部署，此处给出常用 docker-compose 配置文件

```bash
version: '3.6'

services:
  db:
    image: mariadb:10.11
    container_name: seafile-mysql
    restart: unless-stopped
    environment:
      - MYSQL_ROOT_PASSWORD=password
      - MYSQL_LOG_CONSOLE=true
    volumes:
      - ./data/db:/var/lib/mysql
    ports:
      - 3306:3306
    networks:
      - seafile-net
    logging:
      options:
        max-size: "10m"
        max-file: "3"

  memcached:
    image: memcached:1.6
    container_name: seafile-memcached
    restart: unless-stopped
    entrypoint: memcached -m 256
    networks:
      - seafile-net
    logging:
      options:
        max-size: "10m"
        max-file: "3"

  seafile:
    # image: seafileltd/seafile-mc:latest
    image: seafileltd/seafile-mc:11.0.5
    container_name: seafile
    privileged: true
    restart: unless-stopped
    ports:
      - "80:80"
      - "8000:8000"
    volumes:
      - ./data/seafile:/shared
    environment:
      - SEAFILE_ADMIN_PASSWORD=password@admin.com
      - DB_HOST=db
      - DB_ROOT_PASSWD=password
      - SEAFILE_ADMIN_EMAIL=admin@admin.com
      - SEAFILE_SERVER_HOSTNAME=ip
      - SEAFILE_SERVER_LEFSENCRYPT=false
    depends_on:
      - memcached
      - db
      - sdoc-server
      - onlyoffice-documentserver
    networks:
      - seafile-net
      - ldap-net  # Remove this network if LDAP is not used
    logging:
      options:
        max-size: "10m"
        max-file: "3"

  # Remove this section if you do not want to use only office integration
  onlyoffice-documentserver:
    image: onlyoffice/documentserver:8.0.1
    restart: unless-stopped
    container_name: onlyoffice
    privileged: true
    environment:
      - JWT_ENABLED=true
      - JWT_SECRET=seafile

    ports:
      - "8889:80"
    volumes:
        # Optional: see https://manual.seafile.com/deploy/only_office/
      - ./data/onlyoffice/log:/var/log/onlyoffice
      - ./data/onlyoffice/data:/var/www/onlyoffice/Data
      - ./data/onlyoffice/lib:/var/lib/onlyoffice
      - ./data/onlyoffice/db:/var/lib/postgresql
        # - ./data/onlyoffice/local.json:/etc/onlyoffice/documentserver/local.json
    networks:
      - seafile-net
        # logging:
        #   options:
        #     max-size: "10m"
        #     max-file: "3"
  sdoc-server:
    image: seafileltd/sdoc-server:0.5.0
    container_name: sdoc-server
    restart: unless-stopped
    ports:
      # - 8888:80
      # - 443:443
      - 7070:7070
      - 8888:8888
    volumes:
      - ./data/seafile/sdoc-data/:/shared
    networks:
      - seafile-net
    environment:
      - DB_HOST=db
      - DB_PORT=3306
      - DB_USER=root
      - DB_PASSWD=password # Requested, password of MySQL service.
      - DB_NAME=sdoc_db
      - TIME_ZONE=Asia/Shanghai
      - SDOC_SERVER_LETSENCRYPT=false # Whether to use https or not.
      - SEAHUB_SERVICE_URL=http://ip

networks:
  seafile-net:
    name: seafile-net
    ipam:
      driver: default
      config:
        - subnet: 172.31.0.0/16
  ldap-net:  # Remove this network if LDAP is not used
    external: true
    name: ldap-net
```

## 使用

参考官方文档
https://cloud.seafile.com/published/seafile-user-manual/
