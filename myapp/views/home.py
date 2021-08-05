
from flask import (
    current_app,
    abort,
    flash,
    g,
    Markup,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    Response,
    url_for,
)
from flask import Flask, jsonify
from myapp import app, appbuilder, cache
from apispec import yaml_utils
from flask import Blueprint, current_app, jsonify, make_response, request
from flask_babel import lazy_gettext as _
from myapp.views.base import BaseMyappView
import yaml


from flask_appbuilder import ModelView,AppBuilder,expose,BaseView,has_access
from myapp import app, appbuilder

# myapp所有不好归类的视图，比如welcome视图，可以放置在一起


class Myapp(BaseMyappView):
    route_base = '/myapp'
    default_view = 'welcome'   # 设置进入蓝图的默认访问视图（没有设置网址的情况下）

    @expose('/welcome')
    @expose('/profile/<username>/')
    def welcome(self, **kwargs):
        if not g.user or not g.user.get_id():
            return redirect(appbuilder.get_url_for_login)
        msg = 'Hello '+g.user.username+" !"
        # cache.set('msg', msg, timeout=60)
        # cache_value = cache.get('msg')

        # for item1 in appbuilder.menu.get_list():
        #     print(item1)
        # 返回模板
        return self.render_template('hello.html', msg=msg)

    @expose('/home')
    def home(self):
        # 数据格式说明 dict:
        # 'id': 唯一标识,
        # 'type': 类型 一级支持 title | boxlist | list 二级支持 base | text | markdown,
        # 'open': 是否当前页打开 1 从当前窗口打开 默认打开新的标签页,
        # 'url': 点击时打开的链接 仅支持 http(s)://开头,
        # 'cover': 封面图链接 支持base64图片编码,
        # 'content': 内容 支持markdown(需设置类型为markdown),
        # 'data': 嵌套下级内容数组
        data = [
            {
                'id': 1,
                'type': 'title',
                'content': '导航1',
                'data': [],
            }, {
                'id': 2,
                'type': 'boxlist',
                'content': 'Pipelines',
                'data': [{
                    'id': 3,
                    'type': 'text',
                    'open': 1,
                    'url': 'https://www.baidu.com/',
                    'cover': 'https://inews.gtimg.com/newsapp_bt/0/13606847328/1000.jpg',
                    'content': '',
                }, {
                    'id': 4,
                    'type': 'markdown',
                    'url': 'https://www.google.com/',
                    'content': '## <center>Hello Markdown</center>\n\n<center><img src="https://pic3.zhimg.com/v2-2a56e92cf72cd1268d299f47b8d2cf14_r.jpg" width="60%" /></center>',
                }, {
                    'id': 5,
                    'type': 'text',
                    'url': 'https://cn.bing.com/',
                    'content': '这里也可以直接描述文字内容',
                }, {
                    'id': 6,
                    'type': 'text',
                    'url': 'https://www.google.com/',
                    'cover': 'https://pngimg.com/uploads/google/google_PNG102344.png',
                    'content': '',
                }, {
                    'id': 7,
                    'type': 'base',
                    'url': 'https://cn.bing.com/',
                    'cover': 'https://pngimg.com/uploads/aston_martin/aston_martin_PNG55.png',
                    'content': '底部阴影显示1',
                }, {
                    'id': 8,
                    'type': 'base',
                    'url': 'https://cn.bing.com/',
                    'cover': 'https://pngimg.com/uploads/bugatti/bugatti_PNG23.png',
                    'content': '底部阴影显示2',
                }],
            }, {
                'id': 100,
                'type': 'title',
                'content': '导航2',
                'data': [],
            }, {
                'id': 101,
                'type': 'boxlist',
                'content': 'Pipelines',
                'data': [{
                    'id': 102,
                    'type': 'text',
                    'url': 'https://www.baidu.com/',
                    'cover': 'https://lh3.googleusercontent.com/proxy/O9iJmlvwqAMjPqwJf7Vkj_mL5GU9f9KFEhPsRamUV9vs_jAPUavdfJmF-_vyOg7GwjWCw9GKYkIikz8ELFDLJ8xmKQ1kEoIblzUQu3R48L4uUKOxc8LjgsGk3xLHOZU',
                }]
            }
        ]

        # 返回模板
        return self.render_template('home.html', data=data)

    @expose('/search')
    def search(self):
        # 数据格式说明 dict:
        # 'placeholder': string 占位内容
        # 'api': url 搜索调用API
        # 'delay': number 输入延迟时间（毫秒）
        # 'timeout': number 超时时间（秒）
        # 'maxlength': number 最大输入字符长度
        # 'lightColor': color 搜索结果高亮颜色
        # 'logo': bool 是否显示搜索框Logo
        # 'icon': bool 是否显示搜索图标
        data = {
            'placeholder': '请输入关键字...',
            'apikey': 'q',
            'api': 'https://api.bing.com/qsonhs.aspx?type=cb',
            'delay': 1000,
            'timeout': 10,
            'maxlength': 64,
            'lightColor': '#4076e9',
            'logo': True,
            'icon': True,
        }
        # 返回模板
        return self.render_template('search.html', data=data)

    @expose('/app/<id>')
    def app(self, id):
        data = {
            'id': id,
            'url': 'https://whatwebcando.today/camera-microphone.html',
            'target': '',
            'delay': 0,
            'loading': False,
        }
        if id == '2':
            data['url'] = 'https://webglsamples.org/blob/blob.html'
        if id == '3':
            data['url'] = 'http://localhost:8080/'
            data['target'] = '#head_wrapper'  # css选择器语法
            data['delay'] = 500
            data['loading'] = True

        # 返回模板
        return self.render_template('link.html', data=data)

    @expose('/feature/check')
    def featureCheck(self):
        url = request.values.get("url", type=str, default=None)
        # 数据格式说明 dict:
        # 'delay': Integer 延时隐藏 单位: 毫秒 0为不隐藏
        # 'hit': Boolean 是否命中
        # 'target': String 当前目标
        # 'type': String 类型 目前仅支持html类型
        # 'title': String 标题
        # 'content': String 内容html内容
        data = {
            'content': '<video width="100%" height="auto" controls autoplay>\
                            <source src="https://www.runoob.com/try/demo_source/movie.mp4" type="video/mp4">\
                        </video>',
            'delay': 5000,
            'hit': False,
            'target': url,
            'title': '消息提醒弹窗',
            'type': 'html',
        }
        if url == '/myapp/home':
            data['hit'] = True
        return jsonify(data)


# add_view_no_menu添加视图，但是没有菜单栏显示
appbuilder.add_view_no_menu(Myapp)

