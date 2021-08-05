
from flask import request
from flask_appbuilder import expose
from flask_appbuilder.security.decorators import has_access_api
import simplejson as json
from flask_appbuilder.api import BaseApi, expose, rison, safe   # rison 是和json类似更简单的map数据格式
from flask_appbuilder.security.decorators import protect, permission_name
from myapp import appbuilder, db,event_logger
from myapp.utils import core as utils
from .base import api, BaseMyappView, handle_api_exception
from myapp.models.model1 import model1_model2,Model2,Model1

# BaseApi 类包含了所有的公开方法
class ExampleApi(BaseApi):
    resource_name='example'
    version='v1'
    base_permissions=['can_get']   # 该视图类会自动添加的权限绑定，默认不绑定任何权限
    class_permission_name=['ExampleApi']   # 该视图类被添加为视图时的名称
    route_base = '/api'     # 覆盖基础路由/api/{version}/{resource_name},默认是api/v1/$classname_lower

    # expose 注册为蓝图，url为http://localhost:5000/$route_base/greeting
    @expose('/greeting', methods=['POST', 'GET'])
    def greeting(self):
        if request.method == 'GET':
            return self.response(200, message="Hello (GET)")
        return self.response(201, message="Hello (POST)")

    # 编写受权限控制的视图
    # 访问该接口，需要携带token. -H "Authorization: Bearer $TOKEN".
    # token获取：
    # curl -XPOST 'http://localhost:8080/api/v1/security/login'
    # -d '{"username": "root", "password": "admin", "provider": "db"}'
    # -H "Content-Type: application/json"
    @expose('/private')
    @protect()    # 为api启动权限保护。 会在数据库中新建一个can_rison_json的权限，并在视图上建一个这样的视图-权限绑定
    @permission_name('my_Permission')   # 自定义权限名称，而不使用默认的函数名为权限名
    def rison_json(self):
        return self.response(200, message="This is private")


    @expose('/error')
    @safe  # 使用safe装饰器正确处理所有可能的异常，它将为您捕获所有未捕获的异常并返回正确的错误响应
    def error(self):
        raise Exception

# add_api 不会渲染html
appbuilder.add_api(ExampleApi)




# 为model 添加rest api接口
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.api import ModelRestApi

class Model1_ModelApi(ModelRestApi):
    resource_name = 'model1'
    datamodel = SQLAInterface(Model1)
    # 该api自动生成,下面的api和绑定权限,需要有此权限的角色才能调用api
    # /_info    get获取视图的元数据                        can_info
    # /         get,post创建记录                        can_get,can_post,can_put
    # /<id>     get读取记录,delete删除记录,put修改记录     can_get,can_delete



    # 视图元信息包含 (add_columns, add_title, edit_columns, edit_title, filters, permissions)，我们可以利用这些信息设置二次开发前端页面的显示内容

# 通过api接口对后端数据的crud方法参考https://flask-appbuilder.readthedocs.io/en/latest/rest_api.html#get-item

appbuilder.add_api(Model1_ModelApi)


