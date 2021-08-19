from flask import render_template, redirect, jsonify
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView, ModelRestApi
from flask_appbuilder import ModelView, AppBuilder, expose, BaseView, has_access
from flask_babel import gettext as __
from flask_babel import lazy_gettext as _
# 将model添加成视图，并控制在前端的显示
from myapp.models.model1 import model1_model2, Model2, Model1
from flask_appbuilder.actions import action
from flask_appbuilder.models.sqla.filters import FilterEqualFunction, FilterStartsWith, FilterEqual, FilterNotEqual
from wtforms.validators import EqualTo, Length
from flask_babel import lazy_gettext, gettext
from flask_appbuilder.security.decorators import has_access
from myapp import app, appbuilder, cache

from flask import (
    abort,
    flash,
    g,
    Markup,
    redirect,
    render_template,
    request,
    Response,
    url_for,
)
from .base import (
    api,
    BaseMyappView,
    check_ownership,
    CsvResponse,
    data_payload_response,
    DeleteMixin,
    generate_download_headers,
    get_error_msg,
    get_user_roles,
    handle_api_exception,
    json_error_response,
    json_success,
    MyappFilter,
    MyappModelView,
)
from .baseApi import (
    MyappModelRestApi
)
import pysnooper


# 定义数据库视图
class Model1_ModelView(ModelView):
    datamodel = SQLAInterface(Model1)
    # model管理的操作类型
    base_permissions = ['can_add', 'can_edit',
                        'can_delete', 'can_list', 'can_show']
    # 定义创建页面要填写的字段
    add_fieldsets = [
        (
            '属性分组1',
            {'fields': ['attr1', 'attr2', 'attr4']}
        )
    ]
    # 定义编辑页面要填写的字段
    edit_fieldsets = [
        (
            '属性分组1',
            {'fields': ['attr1', 'attr2', 'attr4']}
        )
    ]
    # 定义在前端显示时，model的列，显示成一个新别名
    label_columns = {'attr1': '属性1', 'attr2': "属性2"}
    # 定义前端model list页面显示的列。my_name为自定义样式的一列
    list_columns = ['attr1', 'attr2', 'attr4']
    # 定义单条model记录详情显示的列
    show_fieldsets = [
        (
            '属性分组1',
            {'fields': ['attr1', 'attr2', 'attr4']}
        ),
        (
            '属性分组2',
            {'fields': ['attr1', 'attr2', 'attr4'], 'expanded':False}
        ),
    ]
    # 定义list页面的默认筛选条件的配置
    base_filters = [['attr1', FilterNotEqual, ''], ]   # list获取器
    # 定义list页面的排序方法
    base_order = ('id', 'dasc')
    # 使用自定义模板配置详情页面
    # extra_args = {'name': 'SOMEVALUE'}
    # show_template = 'my_show_template.html'

    # 自定义add/update页面时表单提交自动校验
    validators_columns = {
        # message 为错误时的提示消息
        'attr1': [Length(min=1, max=11, message=gettext('fields length mush 11'))]
    }
    # 为关联字段做自定义查询过滤器。add_form_quey_rel_fields、edit_form_query_rel_fields、search_form_query_rel_fields
    # add_form_query_rel_fields = {'attr3': [['attr1', FilterStartsWith, 'a']]}   # 仅能选择 name字段的值以'家'开头的contact_group。

    # # 自定义 页面模板
    # show_template = 'appbuilder/general/model/show_cascade.html'
    # edit_template = 'appbuilder/general/model/edit_cascade.html'
    # add_template = 'appbuilder/general/model/add_cascade.html'
    # 添加前执行函数
    def pre_add(self, obj):
        pass
    # 添加后执行函数

    def post_add(self, obj):
        pass
    # 更新前执行函数

    def pre_update(self, obj):
        pass
    # 更新后执行函数

    def post_update(self, obj):
        pass
    # 删除前执行函数

    def pre_delete(self, obj):
        pass
    # 删除后执行函数

    def post_delete(self, obj):
        pass

    # 批量操作函数
    @action("muldelete", "Delete", "Delete all Really?", "fa-rocket", single=False)
    def muldelete(self, items):
        if isinstance(items, list):
            self.datamodel.delete_all(items)
            self.update_redirect()
        else:
            self.datamodel.delete(items)
        return redirect(self.get_redirect())


# 添加视图和菜单
appbuilder.add_view(Model1_ModelView, "视图1", icon='fa-list',category='菜单1', category_icon='fa-window-maximize')


# 定义数据表视图
class Model2_ModelView(MyappModelView):
    datamodel = SQLAInterface(Model2)


# 添加model的前后端
appbuilder.add_view(baseview=Model2_ModelView, name="视图2", icon='fa-list',category='菜单1', category_icon='fa-window-maximize')


# 定义数据表视图
class Model2_ModelView_Api(MyappModelRestApi):
    datamodel = SQLAInterface(Model2)
    route_base = '/model2/api'


# 添加model的纯后端接口
appbuilder.add_api(Model2_ModelView_Api)


# 在指定菜单栏下面的每个子菜单中间添加一个分割线的显示。
appbuilder.add_separator("菜单1")


# 只添加菜单栏
appbuilder.add_link(name="Openlink", label=_("链接1"), href="http://www.baidu.com", icon="fa-link",
                    category_icon="fa-window-maximize", category="菜单1", category_label=__("菜单1"))


# 添加菜单
appbuilder.add_link(name="App", label=_("link模板"), href="/myapp/app/2", icon="fa-video-camera",
                    category_icon="fa-window-maximize", category="模板", category_label=__("模板"))
appbuilder.add_link(name="App", label=_("搜索模板"), href="/myapp/search", icon="fa-rocket",
                    category_icon="fa-window-maximize", category="模板", category_label=__("模板"))
