---
title: gitlab
author: flytrap
categories:
  - tech
tags:
  - tech
  - gitlab
  - docker-compose
date: 2024-04-12 10:04:28
---

GitLab 是由 GitLab 公司开发的、基于 Git 的集成软件开发平台。另外，GitLab 且具有 wiki 以及在线编辑、issue 跟踪功能、CI/CD 等功能。
[官网: https://gitlab.com](https://about.gitlab.com)

<!--more-->

## 部署

建议使用 docker 容器化部署，此处给出常用 docker-compose 配置文件

```bash
version: '3.9'
services:
  gitlab:
    image: 'gitlab/gitlab-ce:latest'
    container_name: "gitlab"
    restart: always
    privileged: true
    hostname: 'gitlab'
    environment:
      TZ: 'Asia/Shanghai'
      GITLAB_OMNIBUS_CONFIG: |
        external_url 'http://192.168.1.12'
    ports:
      - '3000:80'
      - '80:80'
      - '443:443'
      - '22:22'
    volumes:
      - './etc:/etc/gitlab'
      - './log:/var/log/gitlab'
      - './opt:/var/opt/gitlab'
```
