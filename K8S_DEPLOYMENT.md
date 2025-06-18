# 金融知识RAG问答系统 Kubernetes 部署指南

## 1. 概述

本项目支持在 Kubernetes 集群中部署，适合生产和开发环境。支持 rag-web、Milvus、MinIO、etcd 的一键部署，Ollama 推荐外部服务。所有组件部署在独立的 `rag-system` 命名空间中。

## 2. 目录结构

```
k8s/
  ├── namespace.yaml            # 命名空间定义
  ├── rag-config.yaml          # 配置 ConfigMap
  ├── rag-web-deployment.yaml  # rag-web Deployment & Service
  ├── rag-web-pvc.yaml        # rag-web 持久化存储声明
  ├── milvus-deployment.yaml   # Milvus/etcd/MinIO 部署与服务
```

## 3. 部署步骤

### 3.1 创建命名空间
```bash
kubectl apply -f k8s/namespace.yaml
```

### 3.2 创建配置
```bash
kubectl apply -f k8s/rag-config.yaml
```

### 3.3 创建持久化存储（PVC）
```bash
kubectl apply -f k8s/rag-web-pvc.yaml
```

### 3.4 部署 Milvus、etcd、MinIO
```bash
kubectl apply -f k8s/milvus-deployment.yaml
```

### 3.5 部署 rag-web
```bash
kubectl apply -f k8s/rag-web-deployment.yaml
```

### 3.6 查看服务
```bash
# 查看所有资源
kubectl get all -n rag-system

# 查看 Pod 状态
kubectl get pods -n rag-system

# 查看服务
kubectl get svc -n rag-system

# 查看配置
kubectl get configmap -n rag-system

# 查看存储
kubectl get pvc -n rag-system
```

rag-web 默认以 NodePort 方式暴露，端口 30500 对应 Web UI。

### 3.7 访问 Web UI
在浏览器访问：
```
# 本地访问
http://localhost:30500

# 局域网访问
http://<NodeIP>:30500
```

## 4. 配置说明

### 4.1 ConfigMap
所有配置都集中在 ConfigMap 中管理，包括：
- Milvus 连接配置
- Ollama 服务配置
- Web 服务配置
- 数据目录配置
- 日志配置

要修改配置：
1. 编辑 `k8s/rag-config.yaml`
2. 应用更改：`kubectl apply -f k8s/rag-config.yaml`
3. 重启 rag-web：`kubectl rollout restart deployment rag-web -n rag-system`

### 4.2 默认配置
- Milvus 服务名：`milvus-standalone`，端口 19530
- Ollama 服务：外部服务，默认 `http://<OllamaIP>:11434`
- Web 服务端口：内部 5000，外部 30500

## 5. 数据持久化

rag-web 的三个目录通过 PVC 持久化：
- `/app/uploads`：上传文件目录
- `/app/data`：数据目录
- `/app/logs`：日志目录

## 6. 常见问题

### 6.1 部署问题
- **Pod 无法调度**：检查命名空间是否正确（`rag-system`）
- **ConfigMap 未找到**：确保 ConfigMap 在正确的命名空间中
- **PVC 绑定失败**：检查存储类和 PVC 配置

### 6.2 服务问题
- **Ollama 服务未连接**：检查 ConfigMap 中的 OLLAMA_HOST 配置
- **Milvus 连接失败**：确保 milvus-standalone 服务在同一命名空间且正常运行
- **Web UI 无法访问**：检查 NodePort 端口（30500）是否被占用或防火墙设置

### 6.3 调试命令
```bash
# 查看 Pod 日志
kubectl logs -n rag-system -l app=rag-web

# 查看 Pod 详细信息
kubectl describe pod -n rag-system -l app=rag-web

# 查看配置
kubectl describe configmap -n rag-system rag-config
```

## 7. 进阶配置

### 7.1 外部服务集成
- Milvus、MinIO、etcd 可替换为外部服务，只需修改 ConfigMap 中的相应配置
- Ollama 默认使用外部服务，通过 ConfigMap 中的 OLLAMA_HOST 配置

### 7.2 网络配置
- 可使用 Ingress 替代 NodePort 暴露服务
- 可配置 TLS 证书实现 HTTPS 访问
- 可通过 NetworkPolicy 限制服务间访问

### 7.3 高可用配置
- 可增加 rag-web 副本数实现负载均衡
- 可配置 HPA 实现自动扩缩容
- 可使用分布式存储提供更好的数据持久化方案

---
如需自定义或遇到问题，欢迎反馈！ 