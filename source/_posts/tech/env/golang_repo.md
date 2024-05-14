---
title: golang 私有包
author: flytrap
categories:
  - tech
tags:
  - tech
  - golang
  - 私有源
  - gitlab
  - mod
date: 2024-05-10 15:10:00
---

```bash
RUN go env -w GOPRIVATE="gitlabIp"
RUN go env -w GONOPROXY="gitlabIp"
RUN go env -w GOINSECURE="gitlabIp"
RUN go env -w GONOSUMDB="gitlabIp"
```
