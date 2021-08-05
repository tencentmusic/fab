#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Project: flow_detect
File：   alarm.py
Description： 
Date：   2017/6/2 15:30
Author： Jeffwan
Copyright 1998 - 2017 TENCENT Inc. All Rights Reserved
modify：
    Jeffwan        2017/6/2       Create
"""
import os
import sys
import time
import uuid
import copy
import ctypes
import threading
import hashlib
import json
from queue import Queue
import binascii
import random
import urllib
import traceback
from Crypto.Cipher import DES
from src.utils.log import Log
from src.utils.http_impl import HttpClient

CONTENT_TYPE_HTML = 1
CONTENT_TYPE_TEXT = 0

class Storage(dict):
    """
    A Storage object is like a dictionary except `obj.foo` can be used
    in addition to `obj['foo']`.
        定义一个容器，可以使用obj.foo的方式来访问其间的数据，实际继承自字典dict
        >>> o = storage(a=1)
        >>> o.a
        1
        >>> o['a']
        1
        >>> o.a = 2
        >>> o['a']
        2
        >>> del o.a
        >>> o.a
        Traceback (most recent call last):
            ...
        AttributeError: 'a'

    """

    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError as k:
            raise AttributeError(k)

    def __repr__(self):
        return '<Storage ' + dict.__repr__(self) + '>'



class Message(Storage):
    """消息基类"""
    MSG_TYPE_WECHAT     =   "wechat"
    MSG_TYPE_QYWX       =   "qywx"
    MSG_TYPE_EAMIL      =   "email"
    MSG_TYPE_TEL        =   "tel"
    MSG_TYPE_SMS        =   "sms"
    MSG_TYPE_GD         =   "gd_event_flow"
    REQ_TIMEOUT         =   5

    def __init__(self, msg_type, url, msg_content):
        """
        消息基类
        :param sender: 消息发送人，只能有一个
        :param recievers: 消息接收人，可以有多个
        :param title:消息标题
        :param msg:消息内容
        """
        self.url            = url
        self.msg_content    = msg_content
        self.msg_type       = msg_type
        self.tof_sys_id     = None
        self.tof_appkey     = None


    def set_auth(self, tof_sys_id, tof_appkey):
        """

        :param tof_sys_id:
        :param tof_appkey:
        :return:
        """
        self.tof_appkey = tof_appkey
        self.tof_sys_id = tof_sys_id


    def send(self):
        """
        发送消息
        :return:
        """
        (content_type, request_data) = self.encode_mutil_data(self.msg_content)
        ##生成校验HTTP header
        auth_header = self.make_http_header()
        auth_header['Content-Type'] = content_type

        ##发送请求
        request = urllib.request.Request(self.url, bytes(request_data, encoding="utf8"), auth_header)
        req = urllib.request.urlopen(request, None, Message.REQ_TIMEOUT)
        ret = req.read()

        ##结果解析
        if ret.find(b"Ret") != -1:
            dict_result = json.loads(ret)
            if dict_result["Ret"] != 0:
                raise Exception("[TofAlarm/sendMsg]Send msg %s error!%s" % (self.msg_type, ret))
        else:
            raise Exception("send msg error, %s" % ret)


    def _pad(self, text, blocksize=8):
        """

        :param text:
        :param blocksize:
        :return:
        """
        """ PKCS#5 Padding """
        padsize = blocksize - (len(text) % blocksize)
        return text + padsize * chr(padsize)


    def des_encypt(self, key, text):
        """
        Function name:encyptyByDes
        Description:加密
        Date:2016年2月1日
        Author:Jeffwan
        Input:strKey, strText
        OutPut:加密
        """
        obj=DES.new(bytes(key, encoding="utf8"), DES.MODE_CBC, bytes(key, encoding="utf8"))
        ciph=obj.encrypt(bytes(self._pad(text), encoding="utf8"))
        return binascii.hexlify(ciph).upper()


    def make_http_header(self):
        """
        Function name:makeHttpHeader
        Description:构造消息http头
        Date:2016年2月1日
        Author:Jeffwan
        http://km.oa.com/group/TOF/articles/show/155846#_AuthApply
        """
        auth_header = {}
        auth_header['appkey'] = self.tof_appkey
        auth_header['random'] = str(random.randint(1,1000000))
        auth_header['timestamp'] = str(int(time.time()))
        key = self.tof_sys_id.ljust(8,'-')
        text = "random%stimestamp%s" % (auth_header['random'], auth_header['timestamp'])
        #caculate signature
        auth_header['signature'] = self.des_encypt(key, text)
        return auth_header


    def encode_mutil_data(self, msg_content):
        """
        Function name:encodeMutilData
        Description:
        Date:2016年2月1日
        Author:Jeffwan
        Input:
        OutPut:
        """
        """
        fields is a  (key, value) elements of dict for regular form fields.
        """
        BOUNDARY = "%s-%d" % (hashlib.md5(str(time.time()).encode()).hexdigest(), random.randint(1,1000000))
        CRLF = '\r\n'
        lines = []
        for (key, value) in list(msg_content.items()):
            if key != "Attachments":
                lines.append('--' + BOUNDARY)
                lines.append('Content-Type: text/plain; charset=utf-8')
                lines.append('Content-Disposition: form-data; name=%s' % key)
                lines.append('')
                lines.append(value)
            else:
                for filename in value:
                    image_name = filename.split("/")[-1]
                    image_type = image_name.split(".")[-1]
                    lines.append('--' + BOUNDARY)
                    # 设置附件类型
                    lines.append('Content-Type: image/' + image_type)
                    lines.append('Content-Disposition: attachment; filename="%s"' % filename)
                    # 设置附件ID
                    lines.append('Content-ID:<%s>' % (image_name))
                    lines.append('')
                    # 获取附件内容
                    content = self.get_attachment_content(filename)
                    lines.append(content)
        lines.append('--' + BOUNDARY + '--')
        lines.append('')
        msg_body = CRLF.join([str(item) for item in lines])
        content_type = 'multipart/form-data; boundary="%s"' % BOUNDARY
        print(msg_body)
        return content_type, msg_body


    def get_attachment_content(self, filename):
        """
        获取附件内容
        :param filename:
        :return:
        """
        with open(filename, "rb") as f:
            s = f.read()
            return s


    def format_users(self, users):
        """

        :param users:
        :return:
        """
        return ";".join(users.replace(",", ";").split(";")).strip().strip(";")



class _WechatMessage(Message):
    """
    微信消息
    """

    def __init__(self, sender, recievers, msg):
        """
        初始化
        :param sender: 消息发件人，需要去http://alarm.weixin.oa.com/，并在tof添加到可信发件人列表中
        :param recievers:消息接收人，多个消息接收人使用分号分隔
        :param title:消息标题
        :param msg:消息内容
        """
        msg_content = {
            "Sender"   :   self.format_users(sender),
            "Rcptto"   :   self.format_users(recievers).split(";"),
            "isText"   :   msg
        }
        Message.__init__(self, Message.MSG_TYPE_WECHAT, None, msg_content)


    def send(self):
        """

        :return:
        """
        url = 'http://api.weixin.oa.com/itilalarmcgi/sendmsg'
        result = HttpClient.post(url, data={"data": json.dumps(self.msg_content)}, content_type="application/x-www-form-urlencoded", json_ret=True, url_encode=True)
        if int(result["errCode"]) != 0:
            Log.debug("send wehcta msg failed, %s" % result["errMsg"])
            raise Exception("send wechat msg failed, %s" % result["errMsg"])



class _WechatChartMessage(Message):
    """
    微信图文消息
    """

    def __init__(self, sender, recievers, title, chart):
        """
        初始化
        :param sender: 消息发件人，需要去http://alarm.weixin.oa.com/，并在tof添加到可信发件人列表中
        :param recievers:消息接收人，多个消息接收人使用分号分隔
        :param title:消息标题
        :param msg:消息内容
        """
        if isinstance(chart, WechatChart) is False:
            raise Exception("chart must be a WechatChart type object")
        msg_content = {
            "Sender": self.format_users(sender),
            "Rcptto": self.format_users(recievers).split(";"),
            "showtype": 1,
            "isAppmsg": {
                        "item1":{
                            "title":title,
                            "itemurl":chart.url,
                            "isText" :chart.msg,
                            "isChart":chart
                        },
                    }

        }
        Message.__init__(self, Message.MSG_TYPE_WECHAT, None, msg_content)
        Message.__init__(self, Message.MSG_TYPE_WECHAT, None, msg_content)


    def send(self):
        """

        :return:
        """
        url = 'http://api.weixin.oa.com/itilalarmcgi/sendmsg'
        result = HttpClient.post(url, data={"data": json.dumps(self.msg_content)}, content_type="application/x-www-form-urlencoded", json_ret=True, url_encode=True)
        if int(result["errCode"]) != 0:
            raise Exception("send wechat msg failed, %s" % result["errMsg"])



class _WechatChartMessage(Message):
    """
    微信图文消息
    """

    def __init__(self, sender, recievers, title, chart):
        """
        初始化
        :param sender: 消息发件人，需要去http://alarm.weixin.oa.com/，并在tof添加到可信发件人列表中
        :param recievers:消息接收人，多个消息接收人使用分号分隔
        :param title:消息标题
        :param msg:消息内容
        """
        if isinstance(chart, WechatChart) is False:
            raise Exception("chart must be a WechatChart type object")
        msg_content = {
            "Sender": self.format_users(sender),
            "Rcptto": self.format_users(recievers).split(";"),
            "showtype": 1,
            "isAppmsg": {
                        "item1":{
                            "title":title,
                            "itemurl":chart.url,
                            "isText" : chart.msg,
                            "isChart":chart
                        },
                    }

        }
        Message.__init__(self, Message.MSG_TYPE_WECHAT, None, msg_content)


    def send(self):
        """

        :return:
        """
        url = 'http://api.weixin.oa.com/itilalarmcgi/sendappmsg'
        result = HttpClient.post(url, data={"data": json.dumps(self.msg_content)}, content_type="application/x-www-form-urlencoded", json_ret=True, url_encode=True)
        if int(result["errCode"]) != 0:
            raise Exception("send wechat msg failed, %s" % result["errMsg"])


class _QywxMessage(Message):
    """
    RTX消息
    """

    def __init__(self, sender, reciever, title, msg):
        """
        初始化
        :param sender: 发件人
        :param reciever: 消息接收人
        :param title: 消息标题
        :param msg: 消息内容
        """
        msg_content = {
            "Title"    :   title,
            "Sender"   :   self.format_users(sender),
            "Receiver" :   self.format_users(reciever),
            "MsgInfo"  :   msg,
            "Priority" :   "1"
        }
        Message.__init__(self, Message.MSG_TYPE_QYWX, "http://oss.api.tof.oa.com/api/v1/Message/SendRTX", msg_content)


class _TelMessage(Message):
    """电话告警"""

    def __init__(self, reciever, title, msg, cc):
        """
        初始化
        :param sender: 发信人
        :param reciever: 接收人
        :param title: 消息标题
        :param msg: 消息内容
        """
        self.rc01           =   '113'
        msg_content = {
            "product_id"    :   "9",
            "event_name"    :   title,
            "content"       :   msg,
            "related_staff" :   reciever,
            "attent_staff"  :   cc,
            "rc01"          :   '113'
        }
        Message.__init__(self, Message.MSG_TYPE_TEL, "http://event.flow.oa.com/eventcenter/createevent", msg_content)



    def send(self):
        """
        发送消息入口
        :param dictParams:
        :return:
        """
        ##发送请求
        ret = HttpClient.post(self.url, data=self.msg_content, timeout=Message.REQ_TIMEOUT, json_ret=False)
        ##结果解析
        if ret.find(b"status_code") != -1:
            dictRet = json.loads(ret)
            if dictRet["status_code"] != 0:
                raise Exception("[TofAlarm/sendMsg]Send msg %s error!%s" % (self.msg_type, dictRet["status_info"]))
        raise Exception("send msg failed, %s" % ret)



class _SmsMessage(Message):
    """短信"""

    def __init__(self, sender, reciever, msg):
        """
        初始化
        :param sender: 发信人
        :param reciever: 接收人
        :param title: 消息标题
        :param msg: 消息内容
        """
        msg_content = {
            "Sender"   :   self.format_users(sender),
            "Receiver" :   self.format_users(reciever),
            "MsgInfo"  :   msg,
            "Priority" :   "1"
        }
        Message.__init__(self, Message.MSG_TYPE_SMS, "http://oss.api.tof.oa.com/api/v1/Message/SendRTX", msg_content)


class _EmailMessage(Message):
    """邮件"""

    def __init__(self, sender, reciever, title, msg, cc, content_format, attachments):
        """
        邮件
        :param sender: 发信人
        :param reciever: 消息接收人
        :param title: 消息标题
        :param msg: 消息内容
        :param cc: 抄送人
        """
        if not msg:
            raise Exception("param msg can not be empty")
        if not isinstance(attachments, list):
            raise Exception("param attachments mush be a list type object with files")
        for file in attachments:
            if not os.path.exists(file):
                raise Exception("file %s does not exists!" % file)
        msg_content = {
            "From"     :   self.format_users(sender),
            "To"       :   self.get_email_by_username(self.format_users(reciever)),
            "CC"       :   self.get_email_by_username(cc),
            "Title"    :   title,
            "Content"  :   msg.replace("\n", "<br />") if content_format == CONTENT_TYPE_TEXT else msg,
            "EmailType":   1,
            "BodyFormat":  content_format,   # 0 文本； 1 html格式
            "Priority" :   1,
            "Location" :   "Tencent",
            "StartTime":   time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),
            "EndTime"  :   time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),
            "Organizer":   sender,
            "Bcc"      :   "",
            "Attachments" : attachments
        }
        Message.__init__(self, Message.MSG_TYPE_EAMIL, "http://oss.api.tof.oa.com/api/v1/Message/SendMail", msg_content)


    def get_email_by_username(self, username):
        """
        Function name:getEmailAddrByRtx
        Description:通过RTX生成email地址，多个rtx用;分隔
        Date:2016年2月24日
        Author:Jeffwan
        Input:strRtx
        OutPut:strEmailAddr
        """
        if not username.strip():
            return ""
        return ";".join(["%s@tencent.com" % reciever.strip()
                         for reciever in
                         username.strip().strip(";").strip(",").replace(",", ";").split(";")])



class MessageHandler(threading.Thread):

    def __init__(self, msg_queue):
        """

        :param msg_queue:
        """
        self.msg_queue  =   msg_queue
        threading.Thread.__init__(self)
        self.daemon = True


    def run(self):
        """
        推送消息
        :return:
        """
        while True:
            try:
                message = self.msg_queue.get()
                message.send()
            except Exception as ex:
                Log.error("send msg failed, %s" % traceback.format_exc())



class _Messager(object):
    """
    消息发送队列
    """
    def __init__(self):
        """
        初始化
        """
        self.msg_queue  = None
        self.use_queue  = False
        self.tof_sys_id = None
        self.tof_appkey = None


    def init(self, tof_appkey, tof_sys_id, use_queue, q_size = 100):
        """
        初始化
        :param type:TaskManager.THREAD 或者TaskManager.PROCESS
        :param max:任务队列同时最大下发数
        """
        self.tof_sys_id = tof_sys_id
        self.tof_appkey = tof_appkey
        self.use_queue  = use_queue
        if use_queue is True:
            self.msg_queue  = Queue(maxsize = q_size)
            MessageHandler(self.msg_queue).start()


    def send_email(self, sender, reciever, title, msg, cc, content_format, attachments):
        """
        发送邮件
        :param sender:
        :param reciever:
        :param title:
        :param msg:
        :param cc:
        :return:
        """
        message = _EmailMessage(sender, reciever, title, msg, cc, content_format, attachments)
        self.__submit(message)


    def send_qywx(self, reciever, title, msg):
        """
        发送企业微信
        :param sender:
        :param reciever:
        :param msg:
        :return:
        """
        #发送企业微信必须传入一个sender参数，这里采用reciever进行替代
        message = _QywxMessage(reciever.strip(";").split(";")[0], reciever, title, msg)
        self.__submit(message)


    def send_weixin(self, sender, reciever, msg):
        """
        发送微信提醒
        :param sender:
        :param reciever:
        :param msg:
        :return:
        """
        message = _WechatMessage(sender, reciever, msg)
        self.__submit(message)


    def send_weixin_chart(self, sender, reciever, title, chart):
        """
        发送微信提醒
        :param sender:
        :param reciever:
        :param msg:
        :return:
        """
        message = _WechatChartMessage(sender, reciever, title, chart)
        self.__submit(message)


    def send_sms(self, sender, reciever, msg):
        """
        发送短信，需要申请内码
        :param sender:
        :param reciever:
        :param msg:
        :return:
        """
        message = _SmsMessage(sender, reciever, msg)
        self.__submit(message)


    def send_tel(self, reciever, title, msg, cc):
        """
        发送电话告警
        :param reciever:
        :param msg:
        :return:
        """
        message = _TelMessage(reciever, title, msg, cc)
        self.__submit(message)



    def __submit(self, message):
        """

        :param message:
        :return:
        """
        if self.tof_sys_id is None or self.tof_appkey is None:
            raise Exception("must call <init> function first")
        #设置鉴权信息
        message.set_auth(self.tof_sys_id, self.tof_appkey)
        if self.use_queue is False:
            message.send()
            return
        #开启了异步队列模式
        self.msg_queue.put(message)



class Messager(object):

    messager = _Messager()

    __instance = None

    def __new__(cls, *args, **kwargs):
        """
        单例模式
        :param args:
        :param kwargs:
        """
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance


    @staticmethod
    def init(tof_app_key, tof_sys_id, use_queue = False, msg_q_size = 100):
        """
        初始化
        tof_app_key和tof_sys_id可以从以下地址查
        http://tof.oa.com/application/views/system_sender.php?sysid=28136
        :param tof_app_key:
        :param tof_sys_id:
        :param use_queue:是否使用消息队列，开启后会有线程在后台重复读取消息数据，因此线程会常驻
        :param msg_q_size:消息发送队列的大小
        :return:
        """
        Messager.messager.init(tof_app_key, str(tof_sys_id), use_queue)


    @staticmethod
    def send_email(sender, reciever, title, msg, cc="", content_format = CONTENT_TYPE_TEXT, attachments = []):
        """

        :param sender: 企业微信用户名或者邮件组
        :param reciever:
        :param title:
        :param msg:
        :param cc: 抄送者
        :return:
        """
        Messager.messager.send_email(sender, reciever, title, msg, cc, content_format, attachments)


    @staticmethod
    def send_qywx(reciever, title, msg):
        """
        发送企业微信消息
        :param sender:
        :param reciever:
        :param title:
        :param msg:
        :return:
        """
        for item_reciever in reciever.strip(";").split(";"):
            Messager.messager.send_qywx(item_reciever, title, msg)


    @staticmethod
    def send_weixin(sender, reciever, msg):
        """
        发送微信消息
        :param sender:微信报警账号，http://alarm.weixin.oa.com/申请
        :param reciever:
        :param msg:
        :return:
        """
        Messager.messager.send_weixin(sender, reciever, msg)


    @staticmethod
    def send_weixin_chart(sender, reciever, title, chart):
        """
        发送微信图文消息
        :param sender:
        :param reciever:
        :param chart:
        :return:
        """
        Messager.messager.send_weixin_chart(sender, reciever, title, chart)


    @staticmethod
    def send_sms(reciever, msg):
        """
        发送短信
        :param sender:
        :param reciever:
        :param msg:
        :return:
        """
        Messager.messager.send_sms(reciever, msg)


    @staticmethod
    def send_tel(reciever, title, msg, cc = ""):
        """

        :param reciever:
        :param msg:
        :return:
        """
        Messager.messager.send_tel(reciever, title, msg, cc)


class WechatChart(dict):
    """
    微信图表消息
    """

    def __init__(self, title, msg, url = ""):
        """

        :param title:
        :param msg:
        :param url:
        """
        self.title  =   title
        self.msg    =   msg
        self.url    =   url
        dict.__init__(self, title = title, desc1 = "", desc2 = "", desc3 = "",
                      label =   [], data1 = [], data2 = [], data3 = [])


    def add_item_stats(self, label, data1 = 0, data2 = 0, data3 = 0):
        """
        往图表中添加单个数据点
        :param label:
        :param data1:
        :param data2:
        :param data3:
        :return:
        """
        self["label"].append(label)
        self["data1"].append(str(data1))
        self["data2"].append(str(data2))
        self["data3"].append(str(data3))


    def set_desc(self, desc1 = "", desc2 = "", desc3 = ""):
        """

        :param desc1:
        :param desc2:
        :param desc3:
        :return:
        """
        self["desc1"] =   desc1
        self["desc2"] =   desc2
        self["desc3"] =   desc3


    def set_stats(self, line_chart_data):
        """

        :param line_chart_data:
        :return:
        """
        for label, data1, data2, data3 in line_chart_data:
            self.add_item_stats(label, data1, data2, data3)




if __name__ == "__main__":
    #初始化参数
    #在server中使用时只需要在配置文件中设置好tof_app_key和tof_sys_id即可，系统会自动进行初始化
    Messager.init("5474f5fa0fe344c8bed8fe516ce1446b", 28136, True)
    #发送企业微信消息
    Messager.send_qywx("jeffwan", "测试标题", "测试企业微信消息1")
    #发送邮件, 发邮件需要先去http://tof.oa.com/application/views/system_sender.php?sysid=28136添加发件人
    Messager.send_email("jeffwan", "jeffwan", "测试邮件标题", "测试邮件内容")
    #发送微信
    #管理页面：https://alarm.weixin.oa.com/itilalarmweb/account_setting?id=2561
    Messager.send_weixin("financial_alarm", "jeffwan", "test wechat msg")
    #发送电话告警
    Messager.send_tel("jeffwan", "测试电话告警", "测试电话告警")
