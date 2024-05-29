---
title: k8s 节点控制
author: flytrap
categories:
  - tech
tags:
  - tech
  - k8s
  - kubernetes
  - join
  - kubeadm
date: 2024-05-29 15:35:20
---

在 Kubernetes 中，节点分为两种， 一种是普通节点，一种是控制平面（control-plane）节点

- 控制平面组件包括 kube-apiserver、kube-controller-manager、kube-scheduler、etcd，是由来支撑平台运行的组件，在集群部署完成时即运行在所有的控制节点上。
- node 节点组件在每个节点上运行，维护运行的 Pod 并提供 Kubernetes 运行环境，

## etcd

- etcd 是兼具一致性和高可用性的键值数据库，是用来保存 Kubernetes 所有集群数据的后台数据库。在生产环境中，为了保证高可用性，一般将 etcd 部署在多个节点上组成集群。

## kube-apiserver

- apiserver 是控制面的前端，对所有资源的操作都要经过 apiserver，apiserver 是无状态的，可以横型扩展，用 Haproxy 或者负载均衡器让多个 apiserver 协同工作。

## kube-scheduler

- scheduler 负责监视新创建的、未指定运行节点（node）的 Pods，选择节点让 Pod 在上面运行。调度决策考虑的因素包括单个 Pod 和 Pod 集合的资源需求、硬件/软件/策略约束、亲和性和反亲和性规范、数据位置、工作负载间的干扰和最后时限。

## kube-controller-manager

- controller-manager 是一系列控制器的集合，这些控制器在逻辑上属于不同的进程，但为了降低复杂性将这些控制器编译在了同一个可执行文件中，控制器包括：

* 节点控制器（Node Controller）: 负责在节点出现故障时进行通知和响应
* 任务控制器（Job controller）: 监测代表一次性任务的 Job 对象，然后创建 Pods 来运行这些任务直至完成
* 端点控制器（Endpoints Controller）: 填充端点(Endpoints)对象(即加入 Service 与 Pod)
* 服务帐户和令牌控制器（Service Account & Token Controllers）: 为新的命名空间创建默认帐户和 API 访问令牌
* 以及其他比如 Pod 管理的 Replication 控制器、Deployment 控制器等数十种类型 API 对象的控制器。

## kube-proxy

- kube-proxy 是集群中每个节点上运行的网络代理， 是实现 Kubernetes 服务（Service） 概念的一部分。
- kube-proxy 维护节点上的网络规则。这些网络规则允许从集群内部或外部的网络会话与 Pod 进行网络通信。
- kube-proxy 有两种模式实现流量转发，分别是 iptables 模式和 ipvs(IP Virtual Server)模式，默认是 iptables 模式，是通过每个节点的 iptables 规则实现的，但随着 service 数量增大，iptables 模式由于线性查找匹配、全量更新等特点，性能会显著下降，因此从 Kubernetes 的 1.8 版本开始引入了 ipvs 模式，ipvs 和 iptables 都是基于 netfilter，但 ipvs 使用 hash 表并且运行在内核态，可以显著提升性能。

## kubelet

- kubelet 是一个在集群中每个节点（node）上运行的代理，负责接收并处理控制节点发来的指令，以及管理当前 node 上 pod 对象的容器，它保证容器（containers）都 运行在 Pod 中。
- kubelet 接收一组通过各类机制提供给它的 PodSpecs，确保这些 PodSpecs 中描述的容器处于运行状态且健康。
- kubelet 不会管理不是由 Kubernetes 创建的容器。
- kubelet 支持从 API server 以配置清单形式接收资源定义，或者从指定的目录加载静态 pod 配置清单，通过容器运行时创建、启动和监事容器。

## 普通节点加入

```bash
kubeadm join <master-ip>:<master-port> --token <your-token> --discovery-token-ca-cert-hash sha256:<your-hash>
```

## 控制平面节点加入

```bash
kubeadm join <master-ip>:<master-port> --token <your-token> --discovery-token-ca-cert-hash sha256:<your-hash> --control-plane --certificate-key <your-certificate-key>
```

## 获取 token

```bash
kubeadm token list
## 获取hash
openssl x509 -pubkey -in /etc/kubernetes/pki/ca.crt | openssl rsa -pubin -outform der 2>/dev/null | openssl dgst -sha256 -hex | sed 's/^.* //'

## 生成新的证书
kubeadm init phase upload-certs --upload-certs

# 完整命令打印
sudo kubeadm token create --print-join-command --certificate-key $(kubeadm certs certificate-key)  # 如果无效，请使用上述命令重新上传证书
```
