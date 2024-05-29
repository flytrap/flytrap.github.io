---
title: istio 配置
author: flytrap
categories:
  - tech
tags:
  - tech
  - k8s
  - kubernetes
  - istio
  - kubeadm
date: 2024-05-29 16:01:05
---

Istio 服务网格
Istio 使用功能强大的 Envoy 服务代理扩展了 Kubernetes，以建立一个可编程的、可感知的应用程序网络。 Istio 与 Kubernetes 和传统工作负载一起使用，为复杂的部署带来了标准的通用流量管理、遥测和安全性。

## 安装

```bash
curl -L https://istio.io/downloadIstio | sh -
```

## 真实 ip 转发

### 生成环境不建议

```bash
kubectl patch svc istio-ingressgateway -n istio-system -p '{"spec":{"externalTrafficPolicy":"Local"}}'
```

### HTTP/HTTPS 负载均衡

```bash
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  meshConfig:
    defaultConfig:
      gatewayTopology:
        numTrustedProxies: 2
```

通过负载均衡器, 添加 ip 转发头
以 nginx 为例

```bash
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

server {
	listen 80 default_server;
	listen [::]:80 default_server;

	server_name _;

	location / {
                proxy_http_version 1.1;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection "upgrade";
                proxy_set_header Host $host;
                proxy_set_header X-Forwarded-For  $proxy_add_x_forwarded_for;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_pass http://192.168.3.161;
        }
}
```
