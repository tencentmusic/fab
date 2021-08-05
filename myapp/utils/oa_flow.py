# -*- coding:utf-8 -*-
"""
des:
create time:
version:
"""
import os
import sys
import json
import time
import hashlib
import requests
from uuid import uuid1

class FlowStorage(object):
    """
    工单的持久化存储，默认存储在./data下的文件中, 适合web后端单点部署的场景
    如果想更改持久化存储介质（例如mysql），你可以继承该类并实现save()和get()方法，并将新的存储介质实例化后传递给OaFlowManager
    """

    def __init__(self, file_path):
        """
        flow临时文件的存放位置
        :param file_path:
        """
        self.file_path = file_path


    def __get_flow_path(self, uuid):
        """

        :param uuid:
        :return:
        """
        if os.path.exists(self.file_path) is False:
            os.mkdir(self.file_path)
        return "%s/%s.dat" % (self.file_path, uuid)


    def save(self, flow):
        """
        保存工单
        :param flow:
        :return:
        """
        flow_path = self.__get_flow_path(flow.uuid)
        if os.path.exists(flow_path) is True:
            raise Exception("flow data file duplicated, flow uuid %s" % flow.uuid)
        with open(flow_path, "w") as file:
            file.write(json.dumps(flow, indent=4))


    def get(self, uuid):
        """
        通过工单的uuid获取工单
        :param uuid:
        :return:
        """
        flow_path = self.__get_flow_path(uuid)
        if os.path.exists(flow_path) is False:
            raise Exception("flow %s does not exists" % uuid)
        with open(flow_path, "r") as file:
            return Flow(**json.loads(file.read()))



class FlowStorage(object):
    """
    流程单信息存储
    """

    def save(self, flow):
        """

        :param flow:
        :return:
        """

    def get(self):
        """

        :return:
        """


class OaFlowManager(dict):
    """
    my.oa.com审批单流程
    """
    ###业务领域分类
    #运营系统
    CATEGORY_OPRSYS = "99511B1EDD8E4EB9B70E7AC1184EEBC2"
    #财经
    CATEGORY_FINACE = "C23D7091B98844659D128773209BBF85"
    #人事
    CATEGORY_HR     = "4EA94BBA64024F2BA647177007A321A5"
    #行政
    CATEGORY_ADMIN  = "6BC9472C4C0D45678E579FE598B7F833"
    #采购
    CATEGORY_BUY    = "5D1700080C64F160F65D64EA20190712"
    #安全中心
    CATEGORY_SEC    = "A40524B5A3C3469DA3D0E876412EF30D"
    #基础
    CATEGORY_BASE   = "773C9AA718CD436581D704DB0B4E2539"
    #测试
    CATEGORY_TEST   = "633C74A559724244A185EA88749C6B97"

    #部署区域
    IDC = "http://idc.esb.oa.com/{appid}/myoa/workitem/{action}"
    OA  = "http://oss.esb.oa.com/{appid}/myoa/workitem/{action}"
    OSS = "http://oss.esb.oa.com/{appid}/myoa/workitem/{action}"
    TEST= "http://test.bus.rio.oa.com:443/{appid}/myoa/workitem/{action}"


    def __init__(self, appid, token, idc = IDC, store = FlowStorage()):
        """
        初始化
        :param appid:
        :param token:
        :param idc:
        """
        self.appid  =   appid if idc != OaFlowManager.TEST else "demo"
        self.token  =   token if idc != OaFlowManager.TEST else "myoatoken"
        self.idc    =   idc
        self.store  =   store
        self.history=   []


    def __signature(self, timestamp):
        """
        生成签名
        :return:
        """
        return hashlib.sha256("{timestamp}{token}{timestamp}".format(timestamp = timestamp, token = self.token)).hexdigest()


    def create(self, flow):
        """
        创建审批单
        :return:
        """
        if isinstance(flow, Flow) is False:
            raise Exception("must give a Flow type object")
        if flow.uuid in self:
            raise Exception("flow %s already created" % flow.uuid)
        timestamp = str(int(time.time()))
        self.__request(self.__get_url(OaFlowManager.create.__name__), timestamp, self.__signature(timestamp), {"work_items" : [flow]})
        self[flow.uuid] = flow
        #持久化
        self.store.save(flow)
        return flow.uuid


    def __actiion(self, uuid, method):
        """

        :param method:
        :return:
        """
        if uuid not in self:
            # 从持久化系统中读取工单内容
            flow = self.store.get(uuid)
        else:
            flow = self[uuid]
        timestamp = str(int(time.time()))
        self.__request(self.__get_url(method), timestamp, self.__signature(timestamp), {
                            "category"          :   flow["category"],
                            "process_name"      :   flow["process_name"],
                            "process_inst_id"   :   flow["process_inst_id"],
                            "activity"          :   "",
                            "handler"           :   "",
                        })
        if uuid in self:del self[uuid]


    def close(self, uuid):
        """
        通过单号的uuid进行结单，用于manager保存在内存中的场景
        当activity和handler为空时，关闭该流程(process_inst_id)下所有单据；当handler为空时，关闭该审批活动(activity)下所有单据；当所有字段都不为空时，关闭唯一单据
        :return:
        """
        self.__actiion(uuid, OaFlowManager.close.__name__)


    def discard(self, uuid):
        """
        撤销
        :return:
        """
        self.__actiion(uuid, OaFlowManager.discard.__name__)


    # def reset(self):
    #     """
    #     在 MyOA 中撤销给定流程实例(process_inst_id)下的所有单据，并创建新单
    #     :return:
    #     """


    def __get_url(self, action):
        """

        :param action:
        :return:
        """
        return self.idc.format(appid = self.appid, action = action)


    def __request(self, url, timestamp, signature, data):
        """

        :param timestamp:
        :param signature:
        :param data:
        :return:
        """
        try:
            response =  requests.post(url, json = data, headers = OaFlowManager.Header(timestamp, signature))
            result = json.loads(response.text)
            if result["code"] != 200:
                raise Exception(response.text)
        except Exception as ex:
            raise Exception(str(response))


    class Header(dict):
        """
        请求头
        """

        def __init__(self, timestamp, signature):
            """

            :param timestamp:
            :param signature:
            """
            dict.__init__(self, timestamp=timestamp, signature=signature)





class Flow(dict):
    """
    审批单
    """

    def __init__(self, process_name, process_inst_id, handler, title, applicant, callback_url = "", activity = "Default", enable_quick_approval = True, enable_batch_approval = True, actions = [], data = [], form = [],
                 list_view = [], detail_view = [], category = OaFlowManager.CATEGORY_OPRSYS, approval_history = [], form_url = None, mobile_form_url = None, uuid = None, tags = {"version": "3.0"}):
        """
        各个参数的格式请参考：http://my.oa.com/docs/myoa3.html#7
        :param category:所属业务领域，单据会被MyOA归类到指定的领域中。可选值为OaWorkFlow下以CATEGORY_开头的几个类属性
        :param process_name:流程名称。标明单据所属的业务系统（流程）。比如：针对报销审批单据，它是费用系统的报销流程创建的。因此其 process_name 为 Cost/ExpenseProcess
        :param process_inst_id:流程实例标识。通常是其对应的业务单据的流水号
        :param activity:单据发生的节点。当前的审批单是报销流程中，申请人直接上级审批。那么这个字段的值即可叫做 申请人直接上级审批，或者对应的英文名称
        :param handler:当前审批单据的处理人的英文名，比如：kevinbyang
        :param title:审批单据的标题，这会展示在审批人的待办列表中
        :param form_url:业务单据的访问地址。审批人点击此地址可以跳转到业务系统的当前单据进行进一步查看和操作
        :param mobile_form_url:业务单据的移动端访问地址。审批人可以在移动端（微信、MOA、RTX、手Q）点击对应的链接打开此单据
        :param callback_url:回调地址。当审批人在MyOA提交了单据后，MyOA会调用此地址告知业务系统审批的结果
        :param enable_quick_approval:是否允许快速审批。此选项只有在审批动作的数量大于或等于2时起效果。当为true时，给定的审批动作的第一个默认理解为同意，第二个默认理解为驳回。审批人可以在待办列表上直接快速审批。如果为false，则在待办列表上无法快速审批，只能打开单据详情进行审批
        :param enable_batch_approval:是否允许批量审批。当为true时，审批人点击“全部同意”后，此单据会默认提交第一个动作。如果为false，则审批人无法通过“全部同意”来审批此单，只能进入此单详情进行审批
        :param applicant:申请人
        :param actions:审批动作，数组类型。
        :param data:单据变量。可以记录一些业务系统传递过来的变量，并在触发回调的时候返回给业务系统。详情请参考 单据变量 一节
        :param form:自定义表单。可以在审批单上展示一个自定义控件的表单。并在回调的时候，把用户的输入结果一并返回给业务系统。详情请参考 自定义表单 一节
        :param list_view:列表视图。在这里的定义的字段会在待办列表中被简要展示出来。如果此字段没有定义，则会使用详情视图的数据来进行填充。详情请参考 列表/详情视图 一节。
        :param detail_view:详情视图。在这里的定义的字段会在待办详情页中被展示出来。详情请参考 列表/详情视图 一节
        """
        dict.__init__(self, process_name = process_name, process_inst_id = process_inst_id, handler = handler, title = title,
                      callback_url = callback_url, applicant = applicant, activity = activity, enable_quick_approval = enable_quick_approval, enable_batch_approval = enable_batch_approval,
                      actions = actions, data = data, form = form, list_view = list_view, detail_view = detail_view, category = category, approval_history = approval_history,
                      form_url = form_url, mobile_form_url = mobile_form_url, tags = tags, uuid = "flow_%s" % str(uuid1()) if uuid is None else uuid)


    @property
    def category(self):
        """

        :return:
        """
        return self["category"]

    @property
    def process_name(self):
        """

        :return:
        """
        return self["process_name"]


    @property
    def process_inst_id(self):
        """

        :return:
        """
        return self["process_inst_id"]


    @property
    def uuid(self):
        """

        :return:
        """
        return self["uuid"]


    class Action(dict):
        """审批动作"""

        def __init__(self, display_name, value):
            """
            填充给Flow对象的actions数组
            :param display_name:动作的展示名称，比如：同意、驳回等
            :param value:动作的值，比如：approve,reject,decline,yes,no等
            """
            dict.__init__(self, display_name = display_name, value = value)


    class ApprovalHistory(dict):
        """
        审批历史
        """

        def __init__(self, approver, action, step, opinion, approval_time, remark):
            """

            :param approver:	审批者的名称
            :param action:      审批者的审批动作，例如同意，拒绝等
            :param step:        审批的步骤
            :param opinion:     审批者的意见
            :param approval_time:审批的时间,格式为:yyyy-MM-ddTHH:mm:ss
            :param remark:      系统备注
            """
            dict.__init__(self, approver = approver, action = action, step = step, opinion = opinion, approval_time = approval_time, remark = remark)


    class Data(dict):
        """
        单据变量
        """

        def __init__(self, key, value):
            """
            data字段是单据的变量，用于业务系统的数据传递。具体来说，data数据由业务系统提交给MyOA系统，MyOA系统在调用业务系统的回调函数时将data数据原样返回。
            :param key:字段标识，业务系统自定义的字段名称
            :param value:字段的值，数组类型
            """
            dict.__init__(self, key = key, value = value)

    class Form(dict):
        """
        业务系统提交的自定义表单，可以在审批单上展示该自定义控件表单，并在回调时一并返回用户的输入结果，目前支持的控件类型为：TextBox,DropDownList,RadioBox,CheckBox,DatePicker。
        """

        def __init__(self, name, values, default_value, description, ui_type, is_required):
            """

            :param name:控件名称
            :param values:控件值的集合，数组类型
            :param default_value:控件的默认值
            :param description:控件的描述
            :param ui_type:控件的类型，目前仅支持五种类型：TextBox,DropDownList,RadioBox,CheckBox,DatePicker
            :param is_required:	提交表单用，决定此字段是否必填，布尔类型
            """
            dict.__init__(self, name = name, values = values, default_value = default_value, description = description, ui_type = ui_type, is_required = is_required)


    class View(dict):
        """

        """
        def __init__(self, key, value):
            """

            :param key:
            :param value:
            """
            dict.__init__(self, key=key, value=value)


if __name__ == '__main__':
    appid = "77c67b808864417e98c1f59fa94f0631"
    token = "500e21ffe21b642d22ec6245e16fdef0fa05ed79ec7276797df8"
    manager = OaFlowManager(appid, token, idc=OaFlowManager.TEST)
    flow = Flow("test_flow", "uuid" + str(time.time()), "jeffwan", "test oa flow", "jeffwan", actions=[Flow.Action("同意", "ok"), Flow.Action("驳回", "no")], callback_url="http://analysis.data.wxpay.oa.com/", list_view=[Flow.View("test_key", "my value")])
    #创建工单
    flow_uuid = manager.create(flow)
    print("flow_uuid:", flow_uuid)




