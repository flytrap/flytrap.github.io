---
title: k8s 问题集锦
author: flytrap
categories:
  - tech
tags:
  - tech
  - k8s
  - problems
date: 2024-04-12 11:35:25
---

收录一些 k8s 使用过程中遇到比较常见的问题，以及解决办法

<!--more-->

## k8s 部分节点不调度

### 示例(集群安装完毕，主节点不调度)

获取 node 状态，都是 ok 的

```bash
kubectl get nodes
NAME       STATUS   ROLES
master1   Ready    control-plane
master2   Ready    control-plane
master3   Ready    control-plane
worker1   Ready    <none>
worker2   Ready    <none>
```

### 查看节点角色及是否支持 schedule, 此处以 master1 为例

```bash
kubectl describe nodes master1 |grep -E '(Roles|Taints)'
```

发现有 NoSchedule Taints
起始就是由于主节点被添加了污点（k8s 的默认行为），只需要移除污点既可解决调度问题
node-role.kubernetes.io/master:NoSchedule
node-role.kubernetes.io/control-plane:NoSchedule

### 移除污点

```bash
# 如果角色是master
kubectl taint nodes master1 node-role.kubernetes.io/master-
# 如果角色是control-plane
kubectl taint nodes master2 node-role.kubernetes.io/control-plane-
```

### 添加污点

```bash
kubectl taint nodes master1 node-role.kubernetes.io/master=:NoSchedule
# 或者
kubectl taint nodes master2 node-role.kubernetes.io/control-plane=:NoSchedule
```

### 知识点（k8s 污点和容忍度）

- 污点（Taints）：定义在节点上，用于拒绝 Pod 调度到此节点，除非该 Pod 具有该节点上的污点容忍度。被标记有 Taints 的节点并不是故障节点。
- 容忍度（Tolerations）：定义在 Pod 上，用于配置 Pod 可容忍的节点污点，K8S 调度器只能将 Pod 调度到该 Pod 能够容忍的污点的节点上。

污点和容忍度（Toleration）相互配合，可以用来避免 Pod 被分配到不合适的节点上。 每个节点上都可以应用一个或多个污点，这表示对于那些不能容忍这些污点的 Pod， 是不会被该节点接受的。

#### 排斥等级

- NoSchedule：没有配置此污点容忍度的新 Pod 不能调度到此节点，节点上现存的 Pod 不受影响。
- PreferNoSchedule：没有配置此污点容忍度的新 Pod 尽量不要调度到此节点，如果找不到合适的节点，依然会调度到此节点。
- NoExecute：没有配置此污点容忍度的新 Pod 对象不能调度到此节点，节点上现存的 Pod 会被驱逐。

#### 容忍度操作符

- Equal：容忍度与污点必须在 key、value 和 effect 三者完全匹配。
- Exists：容忍度与污点必须在 key 和 effect 二者完全匹配，容忍度中的 value 字段要使用空值。
