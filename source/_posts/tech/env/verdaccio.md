---
title: verdaccio 前端私有源
author: flytrap
categories:
  - tech
tags:
  - tech
  - verdaccio
  - docker-compose
  - 前端私有源
date: 2024-05-10 15:10:00
---

我们平时使用 npm publish 进行发布时，上传的仓库默认地址是 npm，公司内部包的管理并不希望发布到公网去，所以需要发布到自己的私有仓库， 之前都是用的 cnpmjs, 由于没有维护了，太老了，所以改用 Verdaccio。 通过 Verdaccio 工具在本地新建一个仓库地址，再把本地的默认上传仓库地址切换到本地仓库地址即可。当 npm install 时没有找到本地的仓库，则 Verdaccio 默认配置中会从 npm 中央仓库下载。

<!--more-->

## 部署

建议使用 docker 容器化部署，此处给出常用 docker-compose 配置文件

```bash
version: '3.1'

services:
  verdaccio:
    image: verdaccio/verdaccio:5.29
    container_name: verdaccio
    networks:
      - node-network
    environment:
      - VERDACCIO_PORT=4873
    ports:
      - '4873:4873'
    volumes:
      - './storage:/verdaccio/storage'
      - './config:/verdaccio/conf'
      - './plugins:/verdaccio/plugins'
networks:
  node-network:
    driver: bridge
```

- storage: 包存储路径
- config: 配置文件路径
- plugins: 插件路径

## 配置文件调整

config/config.yaml

```bash
# https://verdaccio.org/docs/configuration#uplinks
# A list of other known repositories we can talk to
uplinks:
  npmjs:
    url: https://registry.npmjs.org/
  yarn:
    url: https://registry.yarnpkg.com/
  taobao:
    url: https://registry.npmmirror.com/

# Learn how to protect your packages
# https://verdaccio.org/docs/protect-your-dependencies/
# https://verdaccio.org/docs/configuration#packages
packages:
  '@*/*':
    # scoped packages
    access: $all
    publish: $authenticated
    unpublish: $authenticated
    proxy: taobao

  '**':
    # Allow all users (including non-authenticated users) to read and
    # publish all packages
    #
    # You can specify usernames/groupnames (depending on your auth plugin)
    # and three keywords: "$all", "$anonymous", "$authenticated"
    access: $all

    # Allow all known users to publish/unpublish packages
    # (anyone can register by default, remember?)
    publish: $authenticated
    unpublish: $authenticated

    # if package is not available locally, proxy requests to 'npmjs' registry
    proxy: taobao
# To improve your security configuration and avoid dependency confusion
# consider removing the proxy property for private packages
# https://verdaccio.org/docs/best#remove-proxy-to-increase-security-at-private-packages

# https://verdaccio.org/docs/configuration#server
# You can specify the HTTP/1.1 server keep alive timeout in seconds for incoming connections.
# A value of 0 makes the http server behave similarly to Node.js versions prior to 8.0.0, which did not have a
# keep-alive timeout.
# WORKAROUND: Through given configuration you can work around the following issue:
# https://github.com/verdaccio/verdaccio/issues/301. Set to 0 in case 60 is not enough.
server:
  keepAliveTimeout: 60
  # The pluginPrefix replaces the default plugins prefix which is `verdaccio`, please don't include `-`. If `something` is provided
  # the resolve package will be `something-xxxx`.
  # pluginPrefix: something
  # A regex for the password validation /.{3}$/ (3 characters min)
  # An example to limit to 10 characters minimum
  # passwordValidationRegex: /.{10}$/
  # Allow `req.ip` to resolve properly when Verdaccio is behind a proxy or load-balancer
  # See: https://expressjs.com/en/guide/behind-proxies.html
  # trustProxy: '127.0.0.1'

# https://verdaccio.org/docs/configuration#offline-publish
publish:
 allow_offline: true
```

贴出部分配置文件，需要注意的地方有两个

1. 上游源, 我这里添加了一个淘宝源，并指定 npm 代理到淘宝源
2. 发布配置 allow_offline: 允许离线发布, 否则发布会向上游同步

## 使用私有源

```bash
npm install -g nrm --registry http://ip:4873  # 安装nrm
nrm add local http://ip:4873 # 添加本地的npm镜像地址
nrm use local # 使用本地npm地址

# npm set registry http://localhost:4873/
npm i test
```

## 发布

```bash
npm adduser # 添加用户
npm login --registry http://ip:4873 # 登录
npm publish --registry http://ip:4873/
```

浏览器访问: http://ip:4873/ 就可以看到我们发布上去的包了
