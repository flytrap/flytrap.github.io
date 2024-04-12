---
title: jenkins
author: flytrap
categories:
  - tech
tags:
  - tech
  - jenkins
  - jenkins2
  - pipeline
  - docker-compose
date: 2024-04-11 10:04:28
---

Jenkins 提供了软件开发的持续集成服务。它运行在 Servlet 容器中（例如 Apache Tomcat）。它支持软件配置管理（SCM）工具（包括 AccuRev SCM、CVS、Subversion、Git、Perforce、Clearcase 和 RTC），可以执行基于 Apache Ant 和 Apache Maven 的项目，以及任意的 Shell 脚本和 Windows 批处理命令。
[官网: https://www.jenkins.io](https://www.jenkins.io)

<!--more-->

## 部署

建议使用 docker 容器化部署，此处给出常用 docker-compose 配置文件

```bash
version: '3.9'
services:
  jenkins:
    image: jenkins/jenkins:2.440.1
    container_name: jenkins
    # 重启策略：除非手动停止，否则出错会无限重启
    restart: unless-stopped
    privileged: true
    ports:
      # 8080 为 Jenkins 的 Web 端口
      - 8080:8080
      # 50000 为代理节点与主服务器的通信端口？
      - 50000:50000
    volumes:
      # 同步宿主机的时间
      - /etc/timezone:/etc/timezone
      - /usr/local/bin/helm:/usr/local/bin/helm
      - /etc/localtime:/etc/localtime
      # Jenkins 数据目录映射出来，方面操作和备份
      - ./jenkins_home:/var/jenkins_home
      # 把宿主机的 docker 和 docker-compose 给 Jenkins 使用，这样可以直接在 Jenkins 内部打镜像，并直>接操作容器
      - /usr/bin/docker:/usr/bin/docker
      - /var/run/docker.sock:/var/run/docker.sock
      - /usr/bin/docker-compose:/usr/bin/docker-compose
```

当然也可以在容器页面上直接添加容器

访问 :8080 即可打开 Jenkins
此处可以看到初始化密码路径， 就在 jenkins_home/secrets 目录下面

登录之后创建管理员账号

## 插件安装

界面打开: 系统管理-> 插件管理 （/manage/pluginManager/）

- Workspace Cleanup Plugin # 构建完成后清理
- Timestamper # 日志事件显示
- Build Timeout # 构建时间统计
- SSH server # 远程执行
- Pipeline # 流水线
- Localization: Chinese (Simplified) # 汉化(可选)
- Kubernetes CLI Plugin # k8s 命令调用插件(可选)
- GitLab Plugin # gitlab 插件
- Git Parameter Plug-In # 参数构建
- Active Choices # 参数选择

## 流水线基础配置

### 前置配置

1. 添加 gitlab 秘钥
2. “系统管理” -> “系统设置“ -> “Gitlab” 填写 gitlab 信息
3. 添加 k8s 秘钥
4. 添加 docker 秘钥

### 新建任务

1. 新建任务
2. 输入任务名称
3. 选择流水线类型任务
4. GitLab Connection 选择 gitlab Credential
5. 勾选不允许并发构建
6. 选择构建触发器， 获取 webhook 地址 以及 Secret token
7. 填入必要的构建选项， 一般只需要 push event 即可， 也可以定时构建
8. 填入 pipeline 代码

## pipeline 编写

### 构建需求

1. 通过 git tag 标记版本号
2. 推送 tag 触发构建
3. 构建过程中生成版本镜像，helm 并推送至对应仓库
4. 发布 helm 到 k8s 环境中

### 示例代码

```groovy
// helm 发布
def helmDeploy(Map args) {
    // Helm 尝试部署
    if (args.dry_run) {
        println '尝试 Helm 部署，验证是否能正常部署'
        sh 'helm repo update'
        sh "helm upgrade --install ${args.name} --version ${args.version} --set image.repository=${args.repository} --set image.tag=${args.version} chartmuseum/${args.name} --dry-run --debug"
    }
    // Helm 正式部署
    else {
        println '正式 Helm 部署'
        sh 'helm repo update'
        sh "helm upgrade --install ${args.name} --version ${args.version} --set image.repository=${args.repository} --set image.tag=${args.version} chartmuseum/${args.name}"
    }
}

def noticeRtx(String ids, String info) {}

pipeline {
    agent any
    parameters {
        string(name: 'project_name', defaultValue: 'rbac-service', description: '项目名称')
        string(name: 'repo_url', defaultValue: 'git@192.168.1.28:Web/rbac-service.git', description: 'git 仓库')
        // Git Parameter
        gitParameter(name: 'tag_name',
                type: 'PT_TAG',
                branchFilter: 'origin/(.*)',
                defaultValue: '0.0.1',
                selectedValue: 'DEFAULT',
                sortMode: 'DESCENDING_SMART',
                useRepository: env.repo_url,
                description: 'git 标签')
    }

    stages {
        stage('Init') {
            steps {
                sh 'printenv'
                script {
                    if (env.gitlabSourceRepoSshUrl) {
                        env.repo_url = env.gitlabSourceRepoSshUrl
                    }
                    if (env.gitlabSourceRepoName) {
                        env.project_name = env.gitlabSourceRepoName
                    }
                    if (env.gitlabSourceBranch) {
                        env.tag_name = env.gitlabSourceBranch.split('/')[-1]
                    }
                }
                buildName "#${BUILD_NUMBER}-${project_name}-${tag_name}"
            }
        }

        stage('Source') {
            steps {
                checkout([$class: 'GitSCM', branches: [[name: "refs/tags/${tag_name}"]], userRemoteConfigs: [[url: "${repo_url}"]]])
                script {
                    env.imagePath = project_name
                    env.repository = env.imagePath + ':' + env.tag_name
                    env.commitInfo = sh(script:'git log --oneline --no-merges|head -1', returnStdout: true)
                }
                echo 'repository: ' + env.repository
            }
        }

        stage('Build') {
            steps {
                echo 'build repository: ' + env.repository
                script {
                    docker.withRegistry('https://hub.docker.com') {
                        def customImage = docker.build(repository)
                        customImage.push()

                        sh 'docker images | grep citest | awk \'{print $1":"$2}\' | xargs docker rmi -f || true'
                        sh 'docker rmi -f  `docker images | grep \'<none>\' | awk \'{print $3}\'` || true'
                    }
                }
            }
        }

        stage('PackageHelm') {
            steps {
                echo 'package helm'
                sh 'helm package ' + 'chart/' + project_name + ' --app-version ' + env.tag_name + ' --version ' + env.tag_name
                echo 'push helm'
                sh 'helm cm-push ' + env.project_name + '-' + env.tag_name + '.tgz chartmuseum -f'
            }
        }

        stage('Deploy') {
            steps {
                withKubeConfig([credentialsId: 'k8s 密钥id', serverUrl: 'k8s地址']) {
                            // 执行 Helm 方法
                            echo 'Helm 执行部署测试'
                            helmDeploy(dry_run: true ,name: env.project_name , repository: env.imagePath , version: env.tag_name)
                            echo 'Helm 执行正式部署'
                            helmDeploy(dry_run: false, name: env.project_name, repository: env.imagePath, version: env.tag_name)
                }
            }
        }

        stage('Clean') {
            steps {
                cleanWs(
                    cleanWhenAborted: true,
                    cleanWhenFailure: true,
                    cleanWhenNotBuilt: true,
                    cleanWhenSuccess: true,
                    cleanWhenUnstable: true,
                    cleanupMatrixParent: true,
                    disableDeferredWipeout: true,
                    deleteDirs: true
                )
            }
        }
    }

    post {
        always {
            echo env.project_name + ': 项目构建完成'
        }
        success {
            echo env.project_name + ': 构建成功'
            noticeRtx("", env.user + '成功构建了: ' + env.project_name + '\n版本号: ' + env.tag_name + '\n更新内容: \n' + env.commitInfo)
        }
        unstable {
            echo  env.project_name + ': 构建过程报错'
            noticeRtx("", env.user + '构建: ' + env.project_name + '失败了 \n版本号: ' + env.tag_name + '\n更新内容: \n' + env.commitInfo)
        }
        failure {
            echo env.project_name + ': 构建失败'
            noticeRtx("", env.user + '构建: ' + env.project_name + '失败了 \n版本号: ' + env.tag_name + '\n更新内容: \n' + env.commitInfo)
        }
    }
}

```

### 脚本说明

1. 脚本分六个阶段构建
2. 初始化，拉取代码，构建镜像，构建 helm，发布到 k8s，清理
3. 构建完成通知
