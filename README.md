# FAB

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.8.x-blue" alt="Python"></a>
  <a href="https://palletsprojects.com/p/flask/"><img src="https://img.shields.io/badge/Flask-v2.0.x-black" alt="Flask"></a>
  <a href="http://docs.jinkan.org/docs/jinja2/"><img src="https://img.shields.io/badge/Jinja-v2.2.x-green" alt="Jinja"></a>
</p>

# 主要功能

 - 基础元数据的增删改查搜索排序批操作
 - 通用pipeline能力
 - 通用血缘管理的能力
 - 通用可视化的能力
 - 通用首页配置
 
 
# 本地开发

## deploy mysql

```
linux
docker run --network host --restart always --name mysql -e MYSQL_ROOT_PASSWORD=admin -d mysql:5.7
mac
docker run -p 3306:3306 --restart always --name mysql -e MYSQL_ROOT_PASSWORD=admin -d mysql:5.7

```
进入数据库创建一个db
```
CREATE DATABASE IF NOT EXISTS myapp DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
```
镜像构建


```
构建基础镜像（包含基础环境）
docker build -t myapp-base -f install/docker/Dockerfile-base .

使用基础镜像构建生产镜像
docker build -t tencentmusic/myapp:2020.10.01 -f install/docker/Dockerfile .
```

镜像拉取(如果你不参与开发可以直接使用线上镜像)
```
docker pull tencentmusic/myapp:2020.10.01
```

## deploy myapp (docker-compose)

本地开发使用

docker-compose.yaml文件在install/docker目录下，这里提供了mac和linux版本的docker-compose.yaml。
可自行修改
image：刚才构建的镜像
MYSQL_SERVICE：mysql的地址

提示：
 - 1、docker-compose up以后要重启的话，可以先docker-compose down
 - 2、根据部署机器类型选择使用docker-compose-mac.yml还是docker-compose-linux.yml

1) init
```
cd install/docker
STAGE: 'init'
docker-compose -f docker-compose-mac.yml  up
```
will create table and role/permission

2) debug backend
```
STAGE: 'dev'
docker-compose -f docker-compose-mac.yml  up
```
3) Production
```
STAGE: 'prod'
docker-compose -f docker-compose-mac.yml  up
```

部署以后，登录首页会自动调用认证，会自动创建用户，绑定角色（Gamma和rtx同名角色）。

可根据自己的需求为角色授权。

# 生产部署

参考install下方法
