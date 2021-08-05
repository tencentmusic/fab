# kubernetes部署

## 部署元数据组件mysql 已部署可忽略

创建myapp数据库

CREATE DATABASE IF NOT EXISTS myapp DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;

## 部署缓存组件redis 已部署可忽略

## 部署configmap.yaml

包含
entrypoint.sh 镜像启动脚本
config.py  配置文件，需要将其中的配置项替换为自己的

kubectl delete configmap myapp-configmap -n infra
kubectl create configmap myapp-configmap --from-file=config -n infra

## 部署pv-pvc.yaml

在myapp高可用时需要使用分布式存储在存放下载文件。所以需要使用pv/pvc，可根据自己的实际情况部署pv。


## 部署 deploy.yaml
deploy.yaml为myapp的前后端代码
在部署文件中需要修改成自己的环境变量



