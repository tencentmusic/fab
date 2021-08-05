# -*- coding:utf-8 -*-
"""
des: 
create time: 
version: 
"""

import re
from src.utils.tdw_auth_client import TdwAuthClient
from src.utils.http_impl import HttpsClient
from src.utils.utils import to_string
from src.utils.date_time import *


class _MetaTdwAuth(object):
    """
    tdw鉴权客户端
    """
    UPDATE_INTERVAL = 300
    __instance = None

    def __init__(self):
        """

        :param username:
        :param cmk:
        :param service:
        """
        self.username = None
        self.cmk = None
        self.service = None
        self.signature = None
        #签名每5分钟只更新一次
        self.last_update = 0


    def __new__(cls, *args, **kwargs):
        """
        单例模式
        :param args:
        :param kwargs:
        """
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance


    def set(self, username, cmk, service, auth_server):
        """

        :param username:
        :param cmk:
        :param service:
        :return:
        """
        self.username = username
        self.cmk = cmk
        self.service = service
        self.auth_server = auth_server


    def __update(self):
        """

        :return:
        """
        if unix_timestamp() - self.last_update < _MetaTdwAuth.UPDATE_INTERVAL:
            return
        if self.username is None or self.cmk is None or self.service is None:
            return
        self.signature = TdwAuthClient.gen_signature(self.username, self.cmk, self.service, self.auth_server)
        self.last_update = unix_timestamp()


    @property
    def sig(self):
        """

        :return:
        """
        #检查是否需要更新
        self.__update()
        if self.signature is None:
            raise Exception("get tdw auth signature failed, None")
        return self.signature


#存储元数据鉴权信息，默认每五分钟更新一次
MetaTdwAuth = _MetaTdwAuth()


class _MetaDataProtocol(object):
    """
    元数据请求协议定义
    """
    METHOD_GET = "GET"
    METHOD_POST= "POST"

    def __init__(self, url, method=METHOD_GET, params=None, timeout = 60, comment = None, ret_code_key = "code", ret_msg_key = "msg", ret_data_key = "datas"):
        """

        :param url:
        :param method:GET/POST
        :param params:
        """
        self.url = url
        self.method = method.lower()
        self.params = params
        self.timeout = timeout
        self.comment = comment
        self.ret_code_key = ret_code_key
        self.ret_msg_key = ret_msg_key
        self.ret_data_key = ret_data_key


    def __call__(self, **data):
        """

        :param data:
        :return:
        """
        #参数校验
        if self.params is not None:
            self.params.verify(data)
        #请求
        if self.method not in ("get", "post"):
            raise Exception("request method must be get or post")
        method_func = getattr(HttpsClient, self.method)
        try:
            url = self.__url(self.url, data)
            result = method_func(url,
                               data,
                               headers = self.__header(),
                               timeout = self.timeout,
                               json_ret = True)
        except Exception as ex:
            raise Exception("call api %s  failed, %s" % (url, str(ex)))
        try:
            if self.ret_code_key is not None and result[self.ret_code_key] != 0:
                msg = ""
                if self.ret_msg_key is not None:
                    msg = result[self.ret_msg_key]
                raise Exception("call api failed, %s, params:%s" % (msg, str(data)))
            if self.ret_data_key is not None:
                return result[self.ret_data_key]
        except Exception as ex:
            raise Exception("parse result failed, data:%s, msg:%s" % (str(result), str(ex)))


    def __request(self, method, *args, **kwargs):
        """

        :param url:
        :param data:
        :param headers:
        :param timeout:
        :param json_ret:
        :param content_type:
        :return:
        """
        result = method(*args, **kwargs)
        if result["code"] != 0:
            raise Exception("call api failed, %s, params:%s, %s" % (result["msg"], str(args), str(kwargs)))
        return result["datas"]


    def __url(self, url, data):
        """

        :param path:
        :return:
        """
        pattern = r"""#{([a-z0-9_]+)}"""
        variables = re.findall(pattern, url, re.I)
        #替换url中的变量
        for variable in variables:
            if (variable in data) is False:
                raise Exception("param in url named %s does not found in data" % variable)
            url = url.replace("#{%s}" % variable, to_string(data[variable]))
        #用户已经指定了server
        if url.startswith("https://"):
            return url
        return "/".join([TdwMetaData.METADATA_SERVER.strip("/"), url.strip("/")])


    def __header(self):
        """

        :return:
        """
        return {
            "tdw-sign" : MetaTdwAuth.sig
        }


    def create_pyi(self, function_name):
        """

        :return:
        """
        params = ["self"]
        param_comment = []
        if self.params is not None:
            for item_param in self.params:
                params.append("""{param_name}: {param_type} = None""".format(
                    param_name = item_param.name,
                    param_type = item_param.type.__name__
                ))
                param_comment.append(""":param {param_name}:{par_comment}""".format(
                    param_name = item_param.name,
                    par_comment= item_param.comment
                ))
                if len(item_param.child_params) > 0:
                    for item_child_param in item_param.child_params:
                        param_comment.append("""-->:sub-param {param_name}:{par_comment}""".format(
                            param_name=item_child_param.name,
                            par_comment=item_child_param.comment
                        ))
        template = """\n\n    def {function_name}({params_list}):...
        \"\"\"
        {function_comment}
        {param_comment}
        :return: 
        \"\"\"""".format(
            function_name = function_name,
            function_comment = self.comment,
            params_list = ", ".join(params),
            param_comment = "\n        ".join(param_comment)
        )
        return template


class _MetaParams(list):
    """
    接口的参数列表
    """

    def __init__(self, *args):
        """
        初始化
        :param args:
        """
        for item_param in args:
            if not isinstance(item_param, _MetaParam):
                raise Exception("param must be _TdwMetaParam type object")
        list.__init__(self, args)


    def verify(self, data):
        """
        校验参数
        :param data:
        :return:
        """
        errors = []
        for item_param in self:
            # 检查参数是否缺失
            if item_param.name not in data and item_param.required is True:
                errors.append("param %s required, but not given" % item_param.name)
                continue
            error = item_param.verify(data.get(item_param.name, None))
            if error is not None:errors.append(error)
        if len(errors) > 0:
            raise Exception("params verify failed, %s" % ";".join(errors))


class _MetaParam():
    """
    单个参数
    """

    def __init__(self, name, type, required=True, child_params = [], enums = set([]), comment = None):
        """

        :param name:
        :param type:
        :param required:
        """
        self.name = name
        self.type = type
        self.required = required
        self.child_params = child_params
        if isinstance(enums, set) is False:
            raise Exception("param enums must be set type")
        self.enums = enums
        self.comment = comment


    def verify(self, value):
        """

        :param name:
        :param type:
        :param value:
        :return:
        """

        if self.required is False and value is None:
            return
        # 检查类型是否正确
        if not isinstance(value, self.type):
            return "param %s need %s type, but actually %s" % (self.name, self.type, type(value))
        # 检查是否符合枚举类型要求
        if len(self.enums) > 0 and value not in self.enums:
            return "value of param %s must be one of %s" % (self.name, str(self.enums))
        #检查子参数
        errors = []
        if len(self.child_params) > 0:
            if self.type == dict:
                value = [value]
            elif self.type == list:
                pass
            else:
                raise Exception("type %s in param %s does not support child param" % (self.type, self.name))
            #检查子参数
            for item_value in value:
                if not isinstance(item_value, dict):
                    raise Exception("only support child params with dict in list!")
                for item_param in self.child_params:
                    if (item_param.name in item_value) is False and item_param.required is True:
                        errors.append(
                            "child param %s for param %s required, but not found" % (item_param.name, self.name))
                        continue
                    error = item_param.verify(item_value.get(item_param.name, None))
                    if error is not None: errors.append(error)
        return None if len(errors) == 0 else ";".join(errors)



class CommentPage(list):
    """
    生成注释文件
    """
    def __init__(self):
        """
        初始化
        """
        self.append("""# -*- coding:utf-8 -*-
\"\"\"
des: tdw元数据服务客户端
create time: 
version: 
\"\"\"

from typing import Any, Callable, Dict, List, Optional, Tuple, Union, overload

class TdwMetaData:
    \"\"\"tdw元数据服务客户端\"\"\"
    
    def __init__(self, username:str, cmk:str, service:str, meta_server:str = None, auth_server:str = None):
        \"\"\"
        初始化客户端
        :param username: 请求元数据接口的用户名
        :param cmk: tdw鉴权系统中的cmk
        :param service: 请求的服务名称
        :param meta_server:手动指定元数据server地址
        :param auth_server:手动指定auth_server地址
        \"\"\"
""")

    def add_comment(self, comment):
        """

        :param comment:
        :return:
        """
        self.append(comment)
        self.append("\n\n")



    def __repr__(self):
        """

        :return:
        """
        return "\n".join(self)


    def __str__(self):
        """

        :return:
        """
        return "\n".join(self)



class TdwMetaData(object):
    """
    初始化
    接口文档
    http://apidoc.oa.com/doc/%E7%BB%9F%E4%B8%80%E5%85%83%E6%95%B0%E6%8D%AE%E5%AF%B9%E5%A4%96%E6%8E%A5%E5%8F%A3/5ddc8f8803855ee68d272822?version=1.0
    !!!!!注意：cmk从https://tdwsecurity.oa.com这个地址下载
    【服务地址】
        1)元数据服务：
              正式：api.metadata.oa.com
              测试：ping api.metadata.oa.com得到服务器ip，并为其申请8082网络策略
        2)鉴权服务：
              正式：auth.tdw.oa.com
              #测试:开通网络策略
    """
    #接口协议列表， 其中key为接口名称
    PROTOCOLS = dict(
        list_users = _MetaDataProtocol(url="api/atlas/v2/public/tbus/appgroup/listUsersName",
                                       method=_MetaDataProtocol.METHOD_GET,
                                       params=_MetaParams(_MetaParam("appgroup", str, required=True)),
                                       comment="列出应用组下全部用户列表"),
        set_tb_sensitivity = _MetaDataProtocol(url = "/api/atlas/v2/public/config/thive/sensitivity",
                                               method=_MetaDataProtocol.METHOD_POST,
                                               params=_MetaParams(
                                                   _MetaParam("tableSensitivities", list, required=True, child_params=[
                                                       _MetaParam("comment", str, required=True, comment="备注信息"),
                                                       _MetaParam("sensitivity", str, required=True, enums=set({"0", "1", "2"}), comment="要设置的敏感等级：0普通，1敏感，2高敏感"),
                                                       _MetaParam("dbName", str, required=False, comment="库名，可省略，因为外层参数已有"),
                                                       _MetaParam("tableName", str, required=True, comment="要设置的表名")
                                                   ]),
                                                   _MetaParam("group", str, required=False, comment="此次登陆用户的应用组，目前可选"),
                                                   _MetaParam("db", str, required=True, comment="库名"),
                                                   _MetaParam("cluster", str, required=True, comment="库表在的集群"),
                                               ),
                                               comment="设置表的敏感等级"),
        get_bg_storage_cost = _MetaDataProtocol(url = "/api/atlas/v2/public/tdw/cost/storagev2",
                                                method=_MetaDataProtocol.METHOD_POST,
                                                params=_MetaParams(
                                                    _MetaParam("bgName", str, required=True, comment="BG全程，例如：IEG互动娱乐事业群"),
                                                    _MetaParam("planProduct", str, required=False, comment="规划产品，例如：微信支付，可省略")
                                                ),
                                                comment="查询某个BG或产品的存储成本"),
        get_bg_budget = _MetaDataProtocol(url = "/api/atlas/v2/public/tdw/cost/budget",
                                                method=_MetaDataProtocol.METHOD_POST,
                                                params=_MetaParams(
                                                    _MetaParam("bgName", str, required=True, comment="BG全称，例如：IEG互动娱乐事业群"),
                                                    _MetaParam("planProduct", str, required=False, comment="规划产品，例如：微信支付，可省略")
                                                ),
                                          comment="查询某个BG或产品的预算"),
        confirm_user_select_priv = _MetaDataProtocol(url = "/api/atlas/v2/public/urba/#{tdwUser}/tblauthz/select",
                                                method=_MetaDataProtocol.METHOD_POST,
                                                params=_MetaParams(
                                                    _MetaParam("cluster", str, required=True, comment="集群名称，例如：tl"),
                                                    _MetaParam("database", str, required=True, comment="数据库名称"),
                                                    _MetaParam("tableName", str, required=True, comment="表名"),
                                                    _MetaParam("tdwUser", str, required=True, comment="tdw用户名，例如:tdw_jeffwan")
                                                ),
                                                comment="查询某个用户是否有权限读取某张表"),
        get_user_groups = _MetaDataProtocol(url="/api/atlas/v2/public/urba/#{tdwUser}/appgroup",
                                            method=_MetaDataProtocol.METHOD_POST,
                                            params=_MetaParams(_MetaParam("tdwUser", str, required=True, comment="tdw用户名")),
                                            comment="查询用户有权限的应用组：用户所属的应用组"),
        get_user_tables = _MetaDataProtocol(url="/api/atlas/v2/public/urba/#{tdwUser}/thive/granted",
                                            method=_MetaDataProtocol.METHOD_POST,
                                            params=_MetaParams(_MetaParam("tdwUser", str, required=True, comment="tdw用户名"),
                                                               #以下请求参数可选。不加参数，则查询并返回所有有权限的库表；否则返回指定分页的库表
                                                               #返回的每页数据条数
                                                               _MetaParam("size", int, required=False, comment="返回的每页数据条数"),
                                                               #起始偏移量
                                                               _MetaParam("offset", int, required=False, comment="页码偏移"),
                                                               ),
                                            comment="查询用户有权限的库表"
                                            ),
        get_bus_table_with_sensitivity = _MetaDataProtocol(url = "/api/atlas/v2/public/urba/thive/sensity",
                                                           method=_MetaDataProtocol.METHOD_POST,
                                                           params=_MetaParams(
                                                               _MetaParam("productName", str, required=True, comment="规划产品名称,仅限产品owner体验")
                                                           ),
                                                           comment="查看某业务下所有表的敏感等级"
                                                           ),
        set_table_reserve_days = _MetaDataProtocol(url = "/api/atlas/v2/public/config/thive/lifeTime/set",
                                                           method=_MetaDataProtocol.METHOD_POST,
                                                           params=_MetaParams(
                                                               _MetaParam("cluster", str, required=False, comment="集群，默认tl"),
                                                               _MetaParam("dbName", str, required=True, comment="库名"),
                                                               _MetaParam("tableName", str, required=True, comment="tableName"),
                                                               _MetaParam("reservedday", int, required=True, comment="保存天数"),
                                                               _MetaParam("keepLastDayPerMonth", int, required=False, comment="保存策略，默认为1，非必填参数"),
                                                               _MetaParam("userName", str, required=True, comment="请求求改的用户名，例如jeffwan")
                                                           ),
                                                           comment="设置表的生命周期(保存天数)"
                                                   ),
        query_tb_lifetime_modify_state = _MetaDataProtocol(url = "/api/atlas/v2/public/config/thive/lifeTime/approvestat",
                                                           method=_MetaDataProtocol.METHOD_GET,
                                                           params=_MetaParams(
                                                               _MetaParam("approveId", str, required=True, comment="审批单id，由set_table_reserve_days接口返回")
                                                           ),
                                                           comment="查看生命周期设置的审批状态"
                                                           ),
        show_tables = _MetaDataProtocol(url = "/api/atlas/v2/public/tbus/db/listTbsName",
                                                           method=_MetaDataProtocol.METHOD_GET,
                                                           params=_MetaParams(
                                                               _MetaParam("dbName", str, required=True, comment="库名")
                                                           ),
                                                           comment="查询库下的全部表"
                                        ),
        get_table_detail = _MetaDataProtocol(url = "api/atlas/v2/public/tbus/db/tb/point/descInfo",
                                                           method=_MetaDataProtocol.METHOD_GET,
                                                           params=_MetaParams(
                                                               _MetaParam("dbName", str, required=True, comment="库名"),
                                                               _MetaParam("tbName", str, required=True, comment="表名"),
                                                           ),
                                                           comment="查询表的元数据信息",
                                             timeout=300
                                             ),
        get_table_partitions = _MetaDataProtocol(url = "api/atlas/v2/public/tbus/db/tb/point/partitionValue",
                                                           method=_MetaDataProtocol.METHOD_GET,
                                                           params=_MetaParams(
                                                               _MetaParam("dbName", str, required=True, comment="库名"),
                                                               _MetaParam("tbName", str, required=True, comment="表名"),
                                                               _MetaParam("isPrimary", bool, required=True, comment="是否查询主分区"),
                                                               _MetaParam("limit", int, required=True, comment="返回结果条数"),
                                                               _MetaParam("offset", int, required=True, comment="页码偏移")
                                                           ),
                                                           comment="查询表的分区列表",
                                                           ret_code_key=None,
                                                           ret_msg_key=None,
                                                           ret_data_key="entities"
                                                 ),
        list_bg_groups = _MetaDataProtocol(url = "api/atlas/v2/public/tbus/bg/pd/listAgsName",
                                                           method=_MetaDataProtocol.METHOD_GET,
                                                           params=_MetaParams(
                                                               _MetaParam("bgId", str, required=True, comment="BG名称，例如WXG"),
                                                               _MetaParam("pdName", str, required=True, comment="规划产品名称，例如：微信支付"),
                                                           ),
                                                           comment="查询BG或产品下的全部应用组列表"
                                           ),
        show_databases = _MetaDataProtocol(url = "api/atlas/v2/public/tbus/appgroup/listDbsName",
                                                           method=_MetaDataProtocol.METHOD_GET,
                                                           params=_MetaParams(
                                                               _MetaParam("appgroup", str, required=True, comment="用用组id, 例如：g_wxg_wechat_pay")
                                                           ),
                                                           comment="列表应用组下的全部库"
                                           ),
        get_calculate_cost = _MetaDataProtocol(url = "/api/atlas/v2/public/tdw/cost/compute",
                                                           method=_MetaDataProtocol.METHOD_POST,
                                                           params=_MetaParams(
                                                               _MetaParam("bgName", str, required=True, comment="BG全称，例如:CSIG云与智慧产业事业群"),
                                                               _MetaParam("planProduct", str, required=True, comment="规划产品：例如微信支付")
                                                           ),
                                                           comment="查询某个BG/规划产品的计算成本"
                                               ),
        get_us_task_detail = _MetaDataProtocol(url = "api/atlas/v2/public/us/taskDetail",
                                                           method=_MetaDataProtocol.METHOD_GET,
                                                           params=_MetaParams(
                                                               _MetaParam("id", str, required=True, comment="洛子任务id")
                                                           ),
                                                           comment="获取洛子任务的详情信息"
                                               ),
        get_us_task_link = _MetaDataProtocol(url = "api/atlas/v2/public/us/taskLink",
                                                           method=_MetaDataProtocol.METHOD_GET,
                                                           params=_MetaParams(
                                                               _MetaParam("taskId", str, required=True, comment="洛子任务id"),
                                                               _MetaParam("direction", str, required=True, enums=set(["input", "output", "both"]), comment="input表示查任务的上游，output表示查任务的下游，both表示查任务的上下游"),
                                                           ),
                                                           comment="获取洛子任务的上下游"

                                             ),
        get_us_instance_state = _MetaDataProtocol(url = "api/atlas/v2/public/us/taskRun",
                                                           method=_MetaDataProtocol.METHOD_GET,
                                                           params=_MetaParams(
                                                               _MetaParam("taskId", str, required=True, comment="洛子任务id"),
                                                               _MetaParam("startDate", int, required=True, comment="任务运行的数据日期的起始，例如：1561928400000"),
                                                               _MetaParam("endDate", int, required=True, comment="任务运行的数据日期的结束，例如：1571932000000"),
                                                           ),
                                                           comment="获取洛子任务运行状态"
                                                  ),
        get_us_task_belong_view_list = _MetaDataProtocol(url = "api/atlas/v2/public/us/taskBelongViewList",
                                                           method=_MetaDataProtocol.METHOD_GET,
                                                           params=_MetaParams(
                                                               _MetaParam("taskId", str, required=True, comment="洛子任务id")
                                                           ),
                                                           comment="获取洛子任务所属的视图（画布）列表"
                                                         ),
        get_us_task_view = _MetaDataProtocol(url = "api/atlas/v2/public/us/task/view",
                                                           method=_MetaDataProtocol.METHOD_GET,
                                                           params=_MetaParams(
                                                               _MetaParam("viewId", str, required=True, comment="画布id")
                                                           ),
                                                           comment="获取视图（画布）下的所有作业依赖关系"
                                             ),
        list_us_tasks = _MetaDataProtocol(url = "api/atlas/v2/public/us/task/bgAndProduct",
                                                           method=_MetaDataProtocol.METHOD_GET,
                                                           params=_MetaParams(
                                                               _MetaParam("bgId", str, required=True, comment="事业群id，例如WXG"),
                                                               _MetaParam("productName", str, required=True, comment="规划产品名称，例如：微信支付")
                                                           ),
                                                           comment="获取BG或者产品下的全部洛子任务"
                                          ),
        get_table_instore_us_task = _MetaDataProtocol(url = "api/atlas/v2/public/us/task/dbAndTable",
                                                           method=_MetaDataProtocol.METHOD_GET,
                                                           params=_MetaParams(
                                                               _MetaParam("db", str, required=True, comment="数据库名"),
                                                               _MetaParam("table", str, required=True, comment="表名")
                                                           ),
                                                           comment="根据库名和表名获取对应的入库洛子任务"
                                                      ),
        query_user_idex_export_record = _MetaDataProtocol(url = "/api/atlas/v2/public/tdw/access/idex/export/{user}/",
                                                           method=_MetaDataProtocol.METHOD_POST,
                                                           params=_MetaParams(
                                                               _MetaParam("startTime", int, required=True, comment="开始时间unix"),
                                                               _MetaParam("endTime", int, required=True, comment="结束时间unixtime"),
                                                               _MetaParam("user", str, required=True, comment="用户企业微信用户名"),
                                                           ),
                                                           comment="IDEX导出记录：按用户查询"
                                                          ),
        query_tb_idex_export_record = _MetaDataProtocol(url = "/api/atlas/v2/public/tdw/access/idex/dt/export/",
                                                           method=_MetaDataProtocol.METHOD_POST,
                                                           params=_MetaParams(
                                                               _MetaParam("cluster", str, required=True, comment="集群，例如tl"),
                                                               _MetaParam("db", int, required=True, comment="库名"),
                                                               _MetaParam("table", str, required=True, comment="表名"),
                                                               _MetaParam("startTime", int, required=True, comment="开始时间unix"),
                                                               _MetaParam("endTime", int, required=True, comment="结束时间unixtime"),
                                                               _MetaParam("size", int, required=True, comment="导出数据条数"),
                                                               _MetaParam("offset", int, required=True, comment="页码偏移"),
                                                           ),
                                                           comment="IDEX导出记录：按库表查询"
                                                        ),
        get_hive_table_query_record = _MetaDataProtocol(url = "/api/atlas/v2/public/tdw/access/thive/dt/",
                                                           method=_MetaDataProtocol.METHOD_POST,
                                                           params=_MetaParams(
                                                               _MetaParam("cluster", str, required=True, comment="集群，例如tl"),
                                                               _MetaParam("db", int, required=True, comment="库名"),
                                                               _MetaParam("table", str, required=True, comment="表名"),
                                                               _MetaParam("startTime", int, required=True, comment="开始时间unix"),
                                                               _MetaParam("endTime", int, required=True, comment="结束时间unixtime"),
                                                           ),
                                                           comment="hive访问记录：按库表查询"
                                                        ),
        get_hive_user_query_record = _MetaDataProtocol(url = "/api/atlas/v2/public/tdw/access/thive/bu/{userName}",
                                                           method=_MetaDataProtocol.METHOD_POST,
                                                           params=_MetaParams(
                                                               _MetaParam("cluster", str, required=True, comment="集群，例如tl"),
                                                               _MetaParam("db", int, required=True, comment="库名"),
                                                               _MetaParam("table", str, required=True, comment="表名"),
                                                               _MetaParam("startTime", int, required=True, comment="开始时间unix"),
                                                               _MetaParam("endTime", int, required=True, comment="结束时间unixtime"),
                                                               _MetaParam("userName", str, required=True, comment="企业微信用户名")
                                                           ),
                                                           comment="hive访问记录：按用户查询"
                                                       ),
        get_table_query_frequency = _MetaDataProtocol(url = "/api/atlas/v2/public/tdw/access/thive/bu/{userName}",
                                                           method=_MetaDataProtocol.METHOD_POST,
                                                           params=_MetaParams(
                                                               _MetaParam("cluster", str, required=True, comment="集群，例如tl"),
                                                               _MetaParam("db", int, required=True, comment="库名"),
                                                               _MetaParam("table", str, required=True, comment="表名")
                                                           ),
                                                           comment="查询表的访问频率"
                                                      )

    )

    #元数据服务正式环境
    METADATA_SERVER = "https://api.metadata.oa.com"
    #鉴权服务正式环境
    TDW_AUTH_SERVER = "http://auth.tdw.oa.com"


    def __init__(self, username, cmk, service = "metadataservice", meta_server = None, auth_server = None):
        """

        :param username: 请求元数据接口的用户名
        :param cmk: tdw鉴权系统中的cmk
        :param service: 请求的服务名称
        :param meta_server:
        """
        self.username = username
        self.cmk = cmk
        self.service = service
        if meta_server is not None:TdwMetaData.METADATA_SERVER = meta_server
        if auth_server is not None: TdwMetaData.TDW_AUTH_SERVER = auth_server
        MetaTdwAuth.set(username, cmk, service, auth_server)


    def __getattribute__(self, item):
        """

        :param item:
        :return:
        """
        #访问的是接口，返回接口协议
        if item in TdwMetaData.PROTOCOLS:
            return TdwMetaData.PROTOCOLS[item]
        #访问的是类属性
        return object.__getattribute__(self, item)


    def create_pyi(self):
        """

        :return:
        """
        comment = CommentPage()
        for item_func, item_protocol in list(TdwMetaData.PROTOCOLS.items()):
            proto_comment = item_protocol.create_pyi(item_func)
            comment.append(proto_comment)
        print(comment)





