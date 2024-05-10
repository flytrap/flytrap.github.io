---
title: k8s 部署
author: flytrap
categories:
  - tech
tags:
  - tech
  - k8s
  - kubernetes
  - 集群
date: 2024-03-16 10:00:00
---

Kubernetes 是一个可移植、可扩展的开源平台，用于管理容器化的工作负载和服务，可促进声明式配置和自动化。 Kubernetes 拥有一个庞大且快速增长的生态，其服务、支持和工具的使用范围相当广泛。
Kubernetes 这个名字源于希腊语，意为“舵手”或“飞行员”。K8s 这个缩写是因为 K 和 s 之间有 8 个字符的关系。 Google 在 2014 年开源了 Kubernetes 项目。 Kubernetes 建立在 Google 大规模运行生产工作负载十几年经验的基础上， 结合了社区中最优秀的想法和实践。
[官网: https://kubernetes.io](https://kubernetes.io)

主要记录官网的安装部署实践, 以及一些遇到的问题

<!--more-->

## 初始化服务器状态(所有节点)

1. 首先修改 init-config.sh 中的主节点 ip 信息，和 node 节点 ip 信息

```bash
# 初始化配置文件
#! /bin/bash
master_ips=(192.168.1.101 192.168.1.102 192.168.1.103)
node_ips=(192.168.1.104 192.168.1.105)
vip=192.168.1.151  # ip高可用
ethname=ens160  # 网卡名称

cp conf/hosts.tpl hosts  # 需要准备一份host对应关系

haproxy_nodes=""
hostname=""
hostip=$(ip addr show $ethname | grep -w inet | awk '{print $2}' | cut -d'/' -f1)

# 写入hosts
echo "write master hosts"
for ((i=1; i<=${#master_ips[@]}; i++))
do
    # 获取IP地址和索引
    ip="${master_ips[$i-1]}"
    index="$i"
    if [ "$ip" = "$hostip" ]; then
        hostname=master$index
    fi

    # 根据IP创建hosts格式的条目，并追加到文件
    echo "$ip master$index" >> hosts
    haproxy_nodes="${haproxy_nodes}server master$index $ip:6443 check\n        "
done

echo "write node hosts"
for ((i=1; i<=${#node_ips[@]}; i++))
do
    # 获取IP地址和索引
    ip="${node_ips[$i-1]}"
    index="$i"

    if [ "$ip" = "$hostip" ]; then
        hostname=node$index
    fi

    # 根据IP创建hosts格式的条目，并追加到文件
    echo "$ip node$index" >> hosts
done

echo "product haproxy.cfg"
sed "s/{{nodes}}/$haproxy_nodes/g" conf/haproxy.cfg.tpl > haproxy.cfg

echo "product keepalived.conf"
sed "s/{{vip}}/$vip/g" conf/keepalived.conf.tpl > keepalived.conf

echo "product kubeadm-config.yaml"
sed "s/{{vip}}/$vip/g; s/{{hostname}}/$hostname/g; s/{{hostip}}/$hostip/g" conf/kubeadm-config.yaml.tpl > kubeadm-config.yaml

sudo hostnamectl set-hostname "${hostname}"

```

### haproxy.cfg.tpl

```bash
global
        log /dev/log    local0
        log /dev/log    local1 notice
        log 127.0.0.1 local0 err
        chroot /var/lib/haproxy
        stats socket /run/haproxy/admin.sock mode 660 level admin
        stats timeout 30s
        user haproxy
        group haproxy
        maxconn 2000
        ulimit-n 16384
        daemon

        # Default SSL material locations
        ca-base /etc/ssl/certs
        crt-base /etc/ssl/private

        # See: https://ssl-config.mozilla.org/#server=haproxy&server-version=2.0.3&config=intermediate
        ssl-default-bind-ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384
        ssl-default-bind-ciphersuites TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256
        ssl-default-bind-options ssl-min-ver TLSv1.2 no-tls-tickets

defaults
        log     global
        mode    http
        option  httplog
        option  dontlognull
        timeout connect 5000
        timeout client  50000
        timeout server  50000
        timeout http-request 15s
        timeout http-keep-alive 15s
        errorfile 400 /etc/haproxy/errors/400.http
        errorfile 403 /etc/haproxy/errors/403.http
        errorfile 408 /etc/haproxy/errors/408.http
        errorfile 500 /etc/haproxy/errors/500.http
        errorfile 502 /etc/haproxy/errors/502.http
        errorfile 503 /etc/haproxy/errors/503.http
        errorfile 504 /etc/haproxy/errors/504.http

frontend monitor-in
        bind *:33305
        mode http
        option httplog
        monitor-uri /monitor

frontend k8s-master
        bind 0.0.0.0:16443
        bind 127.0.0.1:16443
        mode tcp
        option tcplog
        tcp-request inspect-delay 5s
        default_backend k8s-master

backend k8s-master
        mode tcp
        option tcplog
        option tcp-check
        balance roundrobin
        default-server inter 10s downinter 5s rise 2 fall 2 slowstart 60s maxconn 250 maxqueue 256 weight 100
        {{nodes}}

```

### keepalived.conf.tpl

```bash
! Configuration File for keepalived

global_defs {
    router_id LVS_DEVEL  #虚拟路由名称
    script_user root
    enable_script_security
}

# HAProxy健康检查配置
vrrp_script chk_haproxy {
    script "/usr/bin/killall -0 haproxy"
    interval 5 #  脚本运行周期
    weight -5  #  每次检查的加权权重值
    fall 2
    rise 1
}

# 虚拟路由配置
vrrp_instance VI_1 {
    state BACKUP           #本机实例状态，MASTER/BACKUP，备机配置文件中请写BACKUP
    interface ens160       #本机网卡名称，使用ifconfig命令查看
    virtual_router_id 51   #虚拟路由编号，主备机保持一致
    priority 101           #本机初始权重，备机请填写小于主机的值（例如100）
    advert_int 2           #争抢虚地址的周期，秒
    authentication {
        auth_type PASS
        auth_pass 123456
    }
    virtual_ipaddress {
        {{vip}}/24      # 虚地址IP，主备机保持一致
    }
    track_script {
        chk_haproxy        # 对应的健康检查配置
    }
}
```

### kubeadm-config.yaml

```bash
apiVersion: kubeadm.k8s.io/v1beta3
bootstrapTokens:
  - description: default kubeadm bootstrap token
    groups:
      - system:bootstrappers:kubeadm:default-node-token
    token: n258e9.63nk1rcbcu6422c4
    ttl: 0s
    usages:
      - signing
      - authentication
kind: InitConfiguration
localAPIEndpoint:
  advertiseAddress: {{hostip}}
  bindPort: 6443
nodeRegistration:
  criSocket: unix:///var/run/cri-dockerd.sock
  imagePullPolicy: IfNotPresent
  name: {{hostname}}
  taints:
    - effect: NoSchedule
      key: node-role.kubernetes.io/master
---
apiServer:
  certSANs:
    - {{vip}}
  extraArgs:
    default-watch-cache-size: "500"
    max-mutating-requests-inflight: "500"
    max-requests-inflight: "1000"
    watch-cache-sizes: persistentvolumeclaims#1000,persistentvolumes#1000
  timeoutForControlPlane: 4m0s
apiVersion: kubeadm.k8s.io/v1beta3
certificatesDir: /etc/kubernetes/pki
clusterName: kubernetes
controlPlaneEndpoint: {{vip}}:16443
dns: {}
etcd:
  local:
    dataDir: /var/lib/etcd
imageRepository: registry.k8s.io
kind: ClusterConfiguration
kubernetesVersion: v1.29.2
networking:
  dnsDomain: cluster.local
  podSubnet: 10.244.0.0/16
  serviceSubnet: 10.96.0.0/12
scheduler: {}

```

```bash
# 唯一参数，主机名称(必不可少)
bash install.sh
```

### install.sh

```bash
#!/bin/bash

set -e
hostname=$(hostname)
echo $hostname

# 设置主机名
echo "set host"
# sudo hostnamectl set-hostname "${hostname}"

sudo cp hosts /etc/hosts

# 配置SELINUX
echo "set selinux"
if type setenforce &>/dev/null; then
    sudo setenforce 0 || :
fi

if [ -f /etc/selinux/config ]; then
    sudo sed -i 's/^SELINUX=enforcing$/SELINUX=disable/' /etc/selinux/config
fi

# 禁用内存交换
echo "set swap"
sudo swapoff -a
sudo sed -ir 's/^[^#].*swap.*/#&/' /etc/fstab

# 关闭防火墙
echo "set firewall"
if type ufw &>/dev/null; then
    sudo ufw disable
else
    sudo systemctl stop firewalld.service
    sudo systemctl disable firewalld.service
fi

# 开起网桥
echo "set bridge"

if [ ! -f /etc/sysctl.d/k8s.conf ]; then
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables=1
net.bridge.bridge-nf-call-ip6tables=1
net.ipv4.ip_forward=1
vm.swappiness=0
vm.overcommit_memory=1
vm.panic_on_oom=0
fs.inotify.max_user_watches=89100
fs.file-max=52706963
fs.nr_open=52706963
net.ipv6.conf.all.disable_ipv6=1
net.netfilter.nf_conntrack_max=2310720
EOF
sudo sysctl -q --system
fi

sudo modprobe overlay
sudo modprobe br_netfilter

# 安装docker
echo "install docker"
cd docker
bash install.sh
cd -
sudo cp conf/daemon.json /etc/docker/daemon.json
sudo systemctl restart docker

# 加载镜像
echo "load images"
sudo docker load -i images/k8s-images.tar
sudo docker load < images/calico.tar

echo "install kubeadm"
# 安装 kubelet kubeadm kubectl cri等
# sudo dpkg -i deb/*.deb  # 离线安装
sudo apt-get update
# apt-transport-https 可能是一个虚拟包（dummy package）；如果是的话，你可以跳过安装这个包
sudo apt-get install -y apt-transport-https ca-certificates curl gpg
# 如果 `/etc/apt/keyrings` 目录不存在，则应在 curl 命令之前创建它，请阅读下面的注释。
# sudo mkdir -p -m 755 /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.29/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
# 添加k8s源 此操作会覆盖 /etc/apt/sources.list.d/kubernetes.list 中现存的所有配置。
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.29/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl  # 安装
sudo apt-mark hold kubelet kubeadm kubectl  # 固定版本
# 安装 cri-dockerd
wget https://github.com/Mirantis/cri-dockerd/releases/download/v0.3.12/cri-dockerd_0.3.12.3-0.ubuntu-focal_amd64.deb
sudo dpkg -i cri-dockerd_0.3.12.3-0.ubuntu-focal_amd64.deb
sudo apt install haproxy # 安装haproxy
sudo apt install keepalived # 安装keepalived

# 同步时间
echo "sync time"
sudo ln -snf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
sudo ntpdate ntp.aliyun.com

sudo systemctl enable --now kubelet  # 设置开机启动

echo "install helm"
sudo cp apps/helm /usr/local/bin/
sudo chmod +x /usr/local/bin/helm

if [[ "$hostname" == *"master"* ]]; then

echo "install haproxy keepalived"

# 配置haproxy
sudo cp haproxy.cfg /etc/haproxy/
sudo systemctl restart haproxy

# 配置keepalived
sudo cp keepalived.conf /etc/keepalived/
sudo systemctl stop keepalived
else
echo "remove haproxy keepalived"
sudo apt remove -y keepalived haproxy
fi
```

### 初始化节点

```bash
# 执行完成之后有输出信息，需要复制下来
sudo kubeadm init --config kubeadm-config.yaml --upload-certs
sudo systemctl stop keepalived

# 设置kubectl 命令配置信息(可选)
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

### 复制 join 命令

执行完上述命令，会输出如下信息：
示例如下

```bash
# master 加入命令
kubeadm join 192.168.1.151:16443 --token n258e9.63nk1rcbcu6422c4 --discovery-token-ca-cert-hash sha256:dc4bfbff1b04de4a0ace48379aaf378f62c9b3106ef8a4be20b8e99f0c6d37b3 --control-plane --certificate-key fa9996d07668fd20f367c0b14cae30be50f8826ec47467c6a2116cf0dc3bfabc --cri-socket=unix:///var/run/cri-dockerd.sock

Please note that the certificate-key gives access to cluster sensitive data, keep it secret!
As a safeguard, uploaded-certs will be deleted in two hours; If necessary, you can use
"kubeadm init phase upload-certs --upload-certs" to reload certs afterward.

Then you can join any number of worker nodes by running the following on each as root:

# node 节点加入命令
kubeadm join 192.168.1.151:16443 --token n258e9.63nk1rcbcu6422c4 --discovery-token-ca-cert-hash sha256:4916a116d04b8ac46228bae887445bbe087cac4e8096fc489fe2fc6a6060708e
```

### 部署 master 节点(替换其中的 token,hash,certificate)

```bash
sudo kubeadm join 192.168.1.101:6443 --token n258e9.63nk1rcbcu6422c4 --discovery-token-ca-cert-hash sha256:4916a116d04b8ac46228bae887445bbe087cac4e8096fc489fe2fc6a6060708e --control-plane --certificate-key b5e26ce8cdfa2d92412766d4cd22be7a56283a7ab3c35fca902db37c777dc0ad --cri-socket=unix:///var/run/cri-dockerd.sock
```

### 部署 node 节点(替换其中的 token,hash,certificate)

```bash
kubeadm join 192.168.1.101:6443 --token n258e9.63nk1rcbcu6422c4 --discovery-token-ca-cert-hash sha256:4916a116d04b8ac46228bae887445bbe087cac4e8096fc489fe2fc6a6060708e
```

## 安装网络插件 calico(master 主节点，执行一次)

```bash
wget https://github.com/projectcalico/calico/blob/master/manifests/calico.yaml
kubectl apply -f conf/calico.yaml
```

## 安装集群指标插件

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install kube-state-metrics prometheus-community/kube-state-metrics -n kube-system
kubectl top node  # 测试命令,查看节点资源使用情况
kubectl top pod   # 查看pod资源使用情况
```

到此为止，集群已经安装完成

## 安装 dashboard

```bash
wget https://github.com/jpetazzo/container.training/blob/main/k8s/dashboard-recommended.yaml
kubectl apply -f dashboard-recommended

# 添加访问token
kubectl apply -f conf/dashboard-adminuser.yml
kubectl apply -f conf/admin-role-binding.yaml
kubectl -n kubernetes-dashboard create token admin-user

kubectl proxy #访问地址: http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
```

### ashboard-adminuser.yaml

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: admin-user
  namespace: kubernetes-dashboard
```

### admin-role-binding.yaml

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: admin-user
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
  - kind: ServiceAccount
    name: admin-user
    namespace: kubernetes-dashboard
```

## 安装 nfs(存储可选)

### 安装服务端

```bash
# sudo apt install nfs-kernel-server  ## 服务器端需要安装
sudo mkdir -p /data/nfs
sudo chmod 777 /data/nfs
sudo chown lbjy:lbjy /data/nfs
sudo vim /etc/exports
# 添加配置
# /data/nfs *(rw,sync,no_root_squash)
sudo systemctl restart nfs-kernel-server.service
```

## 安装 rook-ceph(分布式存储，可选)

```bash
helm repo add lbjy http://192.168.1.143:8080
helm repo add rook-release https://charts.rook.io/release
helm install --create-namespace --namespace rook-ceph rook-ceph rook-release/rook-ceph -f conf/rook-ceph.yaml

helm install --create-namespace --namespace rook-ceph rook-ceph-cluster --set operatorNamespace=rook-ceph rook-release/rook-ceph-cluster -f conf/rook-ceph-cluster.yaml
#  获取密码
kubectl -n rook-ceph get secret rook-ceph-dashboard-password -o jsonpath="{['data']['password']}" | base64 --decode && echo
# 测试工具
kubectl -n rook-ceph exec -it deploy/rook-ceph-tools -- bash
ceph status
ceph osd status
ceph df
rados df
```

## 安装 longhorn(分布式存储，可选)

```bash
sudo apt install nfs-common -y
helm repo add longhorn https://charts.longhorn.io
helm repo update
helm install longhorn longhorn/longhorn --namespace longhorn-system --create-namespace --version 1.6.1

USER=deploy; PASSWORD=longhorn.deploy; echo "${USER}:$(openssl passwd -stdin -apr1 <<< ${PASSWORD})" >> auth
kubectl -n longhorn-system create secret generic basic-auth --from-file=auth

```

## 安装 istio(网格,可选)

网格服务，服务治理，好东西，推荐安装

```bash
wget https://github.com/istio/istio/releases/download/1.21.1/istio-1.21.1-linux-amd64.tar.gz
tar -xzvf istio-1.20.3-linux-amd64.tar.gz
cd istio-1.20.3
export PATH=$PWD/bin:$PATH
istioctl install -y  # 安装
kubectl label namespace default istio-injection=enabled  # 开启自动代理

kubectl apply -f samples/addons -n istio-system # 部署loki, Kiali 仪表板、 以及 Prometheus、 Grafana、 还有 Jaeger插件

# 开启访问日志收集
istioctl install -f samples/open-telemetry/loki/iop.yaml --skip-confirmation
kubectl apply -f samples/addons/loki.yaml -n istio-system
kubectl apply -f samples/open-telemetry/loki/otel.yaml -n istio-system

# 开启容器日志收集
helm repo add grafana https://grafana.github.io/helm-charts
helm install promtail grafana/promtail -n istio-system --set config.clients[0].url=http://loki-headless.istio-system/loki/api/v1/push

# 添加网关资源
# kubectl get crd gateways.gateway.networking.k8s.io &> /dev/null || { kubectl kustomize "github.com/kubernetes-sigs/gateway-api/config/crd?ref=v1.0.0" | kubectl apply -f -; }

```
