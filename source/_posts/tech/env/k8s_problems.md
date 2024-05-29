---
title: k8s 问题集锦
author: flytrap
categories:
  - tech
tags:
  - tech
  - k8s
  - kubernetes
  - kubeadm
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

### cordon 停止调度（不可调度，临时从 K8S 集群隔离）

- 影响最小，只会将 node 标识为 SchedulingDisabled 不可调度状态。
- 之后 K8S 再创建的 pod 资源，不会被调度到该节点。
- 旧有的 pod 不会受到影响，仍正常对外提供服务。
- 禁止调度命令"kubectl cordon node_name"。
- 恢复调度命令"kubectl uncordon node_name"。（恢复到 K8S 集群中，变回可调度状态）

### drain 驱逐节点（先不可调度，然后排干）

- 首先，驱逐 Node 上的 pod 资源到其他节点重新创建。
- 接着，将节点调为 SchedulingDisabled 不可调度状态。
- 禁止调度命令"kubectl drain node_name --force --ignore-daemonsets --delete-local-data"
- 恢复调度命令"kubectl uncordon node_name"。（恢复到 K8S 集群中，变回可调度状态）
- drain 方式是安全驱逐 pod，会等到 pod 容器应用程序优雅停止后再删除该 pod。
- drain 驱逐流程：先在 Node 节点删除 pod，然后再在其他 Node 节点创建该 pod。所以为了确保 drain 驱逐 pod 过程中不中断服务（即做到"无感知"地平滑驱逐），必须保证要驱逐的 pod 副本数大于 1，并且采用了"反亲和策略"将这些 pod 调度到不同的 Node 节点上了！也就是说，在"多个 pod 副本+反亲和策略"的场景下，drain 驱逐过程对容器服务是没有影响的。

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

## k8s 时间同步集群故障

重启 kube-system 命名空间下的服务
然后重启对应服务

## kubeadm 加入 master 节点失败

报错: error execution phase check-etcd: etcd cluster is not healthy: context deadli

原因分析:

- 由于该节点已经存在所以无法加入

起因：

- master2 挂掉了，其他节点无法连接该节点
- 尝试通过移除节点，并重新引导节点加入集群的方式去解决

master1 执行

```bash
kubectl delete node master2  # master1 上执行的

### master2上执行
kubeadm reset --cri-socket=unix:///var/run/cri-dockerd.sock
kubeadm join 192.168.1.101:6443 --token n258e9.63nk1rcbcu6422c4 --discovery-token-ca-cert-hash sha256:4916a116d04b8ac46228bae887445bbe087cac4e8096fc489fe2fc6a6060708e --control-plane --certificate-key b5e26ce8cdfa2d92412766d4cd22be7a56283a7ab3c35fca902db37c777dc0ad --cri-socket=unix:///var/run/cri-dockerd.sock
# -->:
# [check-etcd] Checking that the etcd cluster is healthy
# error execution phase check-etcd: etcd cluster is not healthy: failed to dial endpoint https://192.168.3.102:2379 with maintenance client: context deadline exceeded
# To see the stack trace of this error execute with --v=5 or higher
```

```bash
kubectl get pod -n kube-system

kubectl exec -ti etcd-master1 -n kube-system sh
# k8s中etcd使用的是v3的api， 所以要先声明变量
export ETCDCTL_API=3
# 执行命令，查看当前的etcd节点数量
etcdctl --cacert="/etc/kubernetes/pki/etcd/ca.crt" --cert="/etc/kubernetes/pki/etcd/server.crt" --key="/etc/kubernetes/pki/etcd/server.key" member list
# -->:
# 8a67dbc3f58dcef3, started, master3, https://192.168.3.103:2380, https://192.168.3.103:2379, false
# ad8e97d25b4a7a33, started, master1, https://192.168.3.101:2380, https://192.168.3.101:2379, false
# c3d762ff5eaee998, started, master2, https://192.168.3.102:2380, https://192.168.3.102:2379, false
```

发现 master2 节点已经存在

解决:

```bash
etcdctl --cacert="/etc/kubernetes/pki/etcd/ca.crt" --cert="/etc/kubernetes/pki/etcd/server.crt" --key="/etc/kubernetes/pki/etcd/server.key" member remove c3d762ff5eaee998
```

## kubernetes 中 hpa 没生效问题

hpa 就是 Horizontal Pod Autoscaler 的缩写，水平 pod 自动扩容器。也就是可以根据 cpu 和内存指标等，自动扩缩容。

### 确认一下问题

```bash
kubectl get hpa -n istio-system  # 查询hpa情况
# --->:
# NAME                   REFERENCE                         TARGETS          MINPODS   MAXPODS   REPLICAS   AGE
# istio-ingressgateway   Deployment/istio-ingressgateway   <unknown>/80%    1         5         1          35d
# istiod                 Deployment/istiod                 <unknown>/80%    1         5         1          35d

kubectl describe hpa/istio-ingressgateway -n istio-system

# 看到如下警告事件, 起始就是无法获取到当前资源使用情况
# unable to get metrics for resource cpu: unable to fetch metrics from resource metrics API: the server could not find the requested resource (get pods.metrics.k8s.io)
```

### 解决方法

```bash
wget https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

### 在 kind: Deployment 中的 启动命令中添加一行(- --kubelet-insecure-tls)

就像这样

```bash
    spec:
      containers:
      - args:
        - --cert-dir=/tmp
        - --secure-port=10250
        - --kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname
        - --kubelet-use-node-status-port
        - --metric-resolution=15s
        - --kubelet-insecure-tls
```

```bash
kubectl apply -f components.yaml
```

### 现在再看

```bash
kubectl get hpa -n istio-system
# --->:
# NAME                   REFERENCE                         TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
# istio-ingressgateway   Deployment/istio-ingressgateway   4%/80%    1         5         1          35d
# istiod                 Deployment/istiod                 0%/80%    1         5         1          35d
```

## 集群中获取真实 ip

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

## 关于节点挂掉

原因分析:

- 节点通信，证书同步错误，导致节点失联
