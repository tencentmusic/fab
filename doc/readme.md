# 简介
几分钟快速搭建前后端管理控制台，集成oa登录、rbac权限控制、定时调度、缓存、公司平台sdk、前后端接口自动封装、用户行为记录、数据库升级管理、docker镜像、docker-compose调试、k8s部署

# 框架由来
现在对每位开发者全栈能力要求越要越强烈。团队里经常会产出一些工具优化工作效率，工具共享逐步形成管理端控制台，就开始需要有前后端能力介入。此时就要求开发者具有管理控制台的开发能力，而这些控制台大部分又是CURD的基本操作。本开源项目采用fab python框架，部署及生成前后端代码，能够款速部署自己的前后端应用。

目前基于fab的框架开源项目有很多：airflow、superset都是典型的案例

> 目前改造版已经开源到： [https://github.com/tencentmusic/fab](https://github.com/tencentmusic/fab)

# 快速搭建控制台
先来搭建一个看看效果。
![在这里插入图片描述](https://img-blog.csdnimg.cn/349e11a3abf947c3b3b79a1745557b24.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L2x1YW5wZW5nODI1NDg1Njk3,size_16,color_FFFFFF,t_70)

环境准备：

 - 在本地安装docker，docker-compose环境。
 - 你需要有一个mysql数据库，如果没有可以自己部署一个，并创建一个名为myapp的db。
```
linux
docker run --network host --restart always --name mysql -e MYSQL_ROOT_PASSWORD=admin -d mysql:5.7
mac
docker run -p 3306:3306 --restart always --name mysql -e MYSQL_ROOT_PASSWORD=admin -d mysql:5.7

进入数据库创建一个db

CREATE DATABASE IF NOT EXISTS myapp DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
```


下面就可以来安装了。

1、将install/docker/docker-compose.yml文件中STAGE环境变量设置为'init'，然后启动服务docker-compose up， 启动后，会执行entrypoint.sh文件，进行数据库初始化，构建对应的表，添加对应的初始化数据记录。

2、将install/docker/docker-compose.yml文件中STAGE环境变量设置为'dev'，然后启动服务docker-compose up， 启动后，会自动启动前后端。就可以通过http://127.0.0.1:80/打开页面了

![在这里插入图片描述](https://img-blog.csdnimg.cn/51430b0b23ee4f73b3b26766fbc06688.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L2x1YW5wZW5nODI1NDg1Njk3,size_16,color_FFFFFF,t_70)



系统自带了model（数据库表记录）的增删改查接口和页面。所以用户需要做的就只有定义和注册model表结构了。



# oa登录
多用户认证授权的相关逻辑在security.py中，开源版本默认为账号密码登录，若想添加oa认证，可以在MyCustomRemoteUserView中添加对应的函数，并且已添加api访问版的oa认证。用户打开页面时会自动发起oa认证，并自动注册用户，创建和用户同名的角色。 如果你需要修改oa认证，可以修改login函数。用户登录后在个人页面都会有一个秘钥，这个秘钥是用来在api访问时进行认证的。

![在这里插入图片描述](https://img-blog.csdnimg.cn/f843eca7d477428ea0aca57e06313d59.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L2x1YW5wZW5nODI1NDg1Njk3,size_16,color_FFFFFF,t_70)


平台难免会继续向其他三方平台提供api接入能力，只需要其他平台在http访问时的header中提供这个字段，就能正常识别三方平台是哪个用户。后面的授权工作就和web访问相同了。

# 权限管理
登录后还需要进行授权，fab使用rbac进行权限管理。即用户可以绑定不同的角色，角色可以绑定不同的权限。这样用户就具有了指定的权限。

## 用户层：
系统自带了一个admin的用户，每个用户登录时会自动进行注册，同时admin也可以手动创建用户，另外为了更方便admin管理，框架添加了后门链接，可以自己发现。这样管理员可以模拟其他用户登录，查看用户登录后状态。

## 角色层：
系统自带了Admin、Gamma角色，每个用户登录时会自动创建与用户名rtx同名的角色，并且会将每个用户绑定到这个同名角色和Gamma角色上，所以普通用户进来会提示各种没有权限。具有Admin角色的用户具有一切权限，比如为其他用户添加角色，为角色添加权限等。系统自带只有admin用户具有Admin角色，默认账号密码为admin/admin

你可以手动添加各种形式的角色，可以是项目组，可以是组织架构，可以是一类用户...

# 权限层：
权限层包含两部分，视图菜单view/menu和权限类型Base Permissions。即在哪些对象上具有哪些权限，比如在table1上具有add权限，在menu1上具有click权限。

在代码中一般view/menu对应class，Base Permissions对应function。所以视图菜单和权限类型两者之间并不是可以随意绑定的，就像并不是所有的class都有所有的function一样。 系统自带的视图权限可以在web界面上查看。主要是某些菜单的点击权限，某些model(table)的增删改查权限，某些函数的执行权限。

![在这里插入图片描述](https://img-blog.csdnimg.cn/a9a1cb777e1d412ab90d191d34db1d4b.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L2x1YW5wZW5nODI1NDg1Njk3,size_16,color_FFFFFF,t_70)


如果想为自己的函数或者mode注册视图权限，只需要在函数上添加has_access修饰符
```
from flask_appbuilder.security.decorators import has_access
@has_access
def list(self):
  pass
```

 这样用户就需要具有该函数的访问权限才能正常进入该函数，否则会报权限异常。

建议基于/view/base.py中MyappModelView来编写api接口，所有的接口都默认添加了权限注册

# 添加自己的页面和接口
## 1、仅添加菜单链接
```
appbuilder.add_link(
    name="link1",                # 名称，对应视图权限名称
    label=_("link1"),            # web显示名称
    href="http://www.baidu.com", # 链接地址
    category_icon="fa-flask",    # 所在主菜单的图标
    icon="fa-flask",             # 当前子菜单的图表
    category="menu1",            # 主菜单的名称
    category_label=__("menu1")   # 主菜单的web显示名称
    ) 
```

## 2、添加CURD前端界面和后端接口
需要先定义model（表结构），再定义接口视图类，这样就会自动生成前后端代码，最后添加链接到菜单中
```
# 定义model
class Model2(Model):
    __tablename__ = 'model2'
    id = Column(Integer, primary_key=True)
    attr1 = Column(String(50), unique = True, nullable=False)

    def __repr__(self):
        return self.attr1

# 定义数据表视图
class Model2_ModelView(MyappModelView):
    datamodel = SQLAInterface(Model2)


appbuilder.add_view(
    baseview=Model2_ModelView,
    name="submenu2",
    icon = 'fa-address-book-o',
    category = 'menu1',
    category_icon = 'fa-envelope'
    )
```


因为涉及到前端显示，所以涉及的可配置参数比较多，下面列举一些，不过这些也都可以不配置，直接使用默认。
```
# model管理的操作类型
base_permissions
# 定义创建页面分组展示的效果
add_fieldsets
# 定义编辑页面分组展示的效果
edit_fieldsets
# 定义在前端显示时，model的列，显示成一个新别名
label_columns
# 定义前端model list页面显示的列。my_name为自定义样式的一列
list_columns
# 定义单条model记录详情分组展示的效果
show_fieldsets
# 定义list页面的默认筛选条件的配置
base_filters
# 定义list页面的排序方法
base_order
# 自定义add/update页面时表单提交自动校验
validators_columns
# 为关联字段做自定义查询过滤器。add_form_quey_rel_fields、edit_form_query_rel_fields、search_form_query_rel_fields
# add_form_query_rel_fields = {'attr3': [['attr1', FilterStartsWith, 'a']]}   # 仅能选择 name字段的值以'家'开头的contact_group。
# # 自定义 页面模板
# show_template = 'appbuilder/general/model/show_cascade.html'
# edit_template = 'appbuilder/general/model/edit_cascade.html'
# add_template = 'appbuilder/general/model/add_cascade.html'
# 添加前执行函数
def pre_add(self, obj):
# 添加后执行函数
def post_add(self,obj):
# 更新前执行函数
def pre_update(self, obj):
# 更新后执行函数
def post_update(self,obj):
# 删除前执行函数
def pre_delete(self, obj):
# 删除后执行函数
def post_delete(self,obj):
# 批量操作函数
@action("muldelete", "Delete", "Delete all Really?", "fa-rocket", single=False)
def muldelete(self, items):
```

## 3、添加CURD纯后端接口
添加CURD纯后端的方法与添加前后端的方法相似，都是先定义model，定义视图类，注册api接口。
```
# 定义数据表视图
class Model3_ModelView_Api(MyappModelRestApi):
    datamodel = SQLAInterface(Model2)
    route_base = '/model2/api'

appbuilder.add_api(Model3_ModelView_Api)
 ```

## 4、添加自定义后端接口
添加纯后端的接口。需要自己先定义一批接口，然后将类注册到系统中。
```

class Myapp(BaseMyappView):
    route_base='/myapp'
    default_view = 'welcome' 

    @expose('/welcome')
    def welcome(self):
        if not g.user or not g.user.get_id():
            return redirect(appbuilder.get_url_for_login)
        msg = 'Hello '+g.user.username+" !"
        return self.render_template('hello.html', msg=msg)

# add_view_no_menu添加视图，但是没有菜单栏显示
appbuilder.add_view_no_menu(Myapp)
```
##  5、flask的传统方法
因为fab是基于flask开发的，所以你也可以用flask的任何方法，例如注册路由。
```
@app.route("/health")
def health():
    return "OK"
```
# 公司组件api
为了能更方便的与公司内部平台结合，在utils文件夹下添加了较多工具类，可以方便直接访问公司平台

# 定时调度能力
管理控制台难免会有很多的离线定时任务或异步任务。框架集成了celery，可以实现定时任务、异步任务的发起和执行。在config.py配置文件CeleryConfig类中，你可以配置定时框架参数和你要执行的定时任务参数。系统默认配置的是redis作为任务队列和结果存储数据库。

## 任务编写：
任务的编写在tasks目录下，框架下配置了一个示例任务tasks/schedules.py中，并添加了任务结果的微信推送。
```
# 配置celery任务
@celery_app.task(name="task.task_name1", bind=True)
def task_name1(task):
  pass
```
## 配置任务调度参数：
在config.py配置文件的CeleryConfig类中，CELERY_ANNOTATIONS用来配置单个任务在执行时的限制条件：
```
# 任务的限制，key是celery_task的name，值是限制配置
CELERY_ANNOTATIONS = {
    'task.task_name1': {
        'rate_limit': '1/s',     # 任务的调度速率限制
        'time_limit': 1200,      # 任务的运行时长限制，直接退出
        'soft_time_limit': 1200, # 任务的运行时长限制，会报异常，可以catch
        'ignore_result': True,
    },
}
```
 CELERYBEAT_SCHEDULE用来配置并发任务的限制条件：
```
# 定时任务的配置项，key为celery_task的name，值是调度配置
CELERYBEAT_SCHEDULE = {
    'task_task1': {
        'task': 'task.task_name1',     # 控制任务
        'schedule': 10.0,              # 调度周期
        # 'schedule': crontab(minute='1', hour='*'),   # 调度周期
    }
}
```
## 任务的调度
有了任务的定义和运行配置，下面就是怎么根据这些配置定时产生任务。框架中定时任务是基于celery的，可以直接使用celery命令启动进程产生定时任务。
```
celery beat --app=myapp.tasks.celery_app:celery_app --loglevel=info
```
 在docker-compose.yaml中包含了beat服务，该服务就是用来产生定时任务，推送到redis的。

## 任务的执行
定时任务发送到redis以后，需要有worker接收器执行任务。同样是使用celery命名启动多个worker，并发执行任务
```
celery worker --app=myapp.tasks.celery_app:celery_app --loglevel=info --pool=prefork -Ofair -c 4
```
在docker-compose.yaml中包含了worker服务，该服务会创建worker容器接收并执行任务。 

# 缓存
框架包含了缓存的配置，在config.py文件中CACHE_CONFIG为缓存的配置，系统默认配置使用redis做为缓存数据库，并做好了所有的配置需要，在代码中使用缓存很简单。
```
from myapp import cache    # 引入
cache.set('msg', msg, timeout=60)   # 设置
cache_value = cache.get('msg')    # 读取
```
# 用户行为记录
添加用户行为记录是肯定需要的日志功能。框架已经将代码集成好，如果想收集用户对指定函数的的访问记录，只需要在函数上添加修饰符。会将用户或者api访问的行为记录到数据表logs中
```
from myapp import event_logger
@event_logger.log_this
def list(self):
    pass
```
![在这里插入图片描述](https://img-blog.csdnimg.cn/37b0f448c2f746e2b55beb5f53df322a.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L2x1YW5wZW5nODI1NDg1Njk3,size_16,color_FFFFFF,t_70)

这样用户访问以后就可以在action log中看到哪个用户什么时间访问了哪个路径做了什么操作和传递的参数。

# 数据库结构升级和回滚
基于开源框肯定要做一个model的新增或修改，也就是对应了数据表的变更。框架基于Flsak-Migrate集成了数据库结构的升级和回滚。前提是，系统引入myapp/__init__.py时是可以引入该model的。比如在__init__.py最下面引入了views，每个view又引入了对应的model，这样这些被引入的model，就可以被系统识别到，用来判断升级或回滚策略。

数据库的管理文件在myapp/migrations下面。所有的升级记录在myapp/migrations/versions目录下面。如果你新增或修改了model，并且可以被系统发现，那只需要在容器的/home/myapp/目录下面，执行
```
myapp db migrate   # 生成对应版本数据库表的升级文件到versions文件夹下
```
这样，系统就会对比你当前连接的数据库中的所有表的结构和你代码中的定义的表结构有啥区别，需要做什么升级操作才能使数据库跟代码中的表结构一致，并生成升级文件到versions目录下。所以你的数据库一定不能随意手动修改，那么数据库的升级记录文件就不具有连贯性了。

有了升级记录文件，就可以直接直接使用下面的命令进行数据库升级了。
```
myapp db upgrade     # 数据库表同步更新到mysql
```
# docker镜像封装
项目包含了docker镜像封装，为了能方便代码调试快速迭代更新，镜像包含两部分：

1、install/docker/Dockerfile-base为基础环境的封装，封装耗时比较久，但是环境部分内容改动比较小，所以封装一次可以保持好久不用变动，是代码运行+调试的基本环境。

2、install/docker/Dockerfile在上面基础环境镜像的基础上加封代码，因为只是copy代码，所以封装比较快，更适合短周期迭代更新。

# 本地调试
由于本框架涉及到多个容器组件，所以在本地调试使用docker-compose进行启动，当然你也可以使用docker-compose进行生产线部署，只不过该部署方案只能在单机上进行，无法避免单点故障的问题。

单机部署调试的部署配置在install/docker/docker-compose.yaml文件中，其中包含redis/myapp/beat/worker等服务，另外还需要自己提供mysql数据库。如果的控制台需求比较简单，可以在docker-compose.yaml中注释掉你不需要的部分。

另外为了方便调试，一般会将代码目录、配置文件，甚至本地python库挂载到容器中
```
- ../../myapp/:/home/myapp/myapp/  
- ./entrypoint.sh:/entrypoint.sh
- ./config.py:/home/myapp/myapp/config.py
```
这样你就可以直接在自己的ide中编辑，然后容器中也能检测到自动加载执行了。注意dev模式能自动检测文件变更热加载，prod模式不能自检测，需要手动重启。 

# k8s高可用部署
本地调试完成后就需要上生产线，如果你的应用比较简单，或者只是内部使用，可以使用上面的方法使用docker-compose部署。不过我们更推荐直接部署上云，项目install/kubernetes/目录中包含了项目所需应用的全部k8s部署文件。这个可能需要你有一定的k8s基础技能。所以不再赘述，可直接参考https://github.com/tencentmusic/fab/tree/master/install/kubernetes
