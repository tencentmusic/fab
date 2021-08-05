# -*- coding:utf-8 -*-
"""
des: 
create time: 
version: 
"""


import json
import time
import math
import random
from urllib.parse import quote
from src.utils.http_impl import HttpClient

#默认的tdbus manager地址，一般不会改变。idc适用。
DEFAULT_TDBUS_MANAGER_HOST = "10.213.2.4:8099"
#服务端ip地址的更新频率
SERVER_IP_FRESH_INTERVAL = 300

class TdbankHttpClient(object):
    """
    tdbank http接入客户端
    """

    def __init__(self, bid, tdbus_manager_host = DEFAULT_TDBUS_MANAGER_HOST):
        """
        初始化
        :param bid:tdbank上的业务id
        :param tdbus_manager_host:
        """
        self.bid             =   bid
        self.tdbus_manager   =   tdbus_manager_host
        self.last_update     =   0
        self.server_addr     =   None
        self.manager_address =   "http://{tdbus_manager_host}/api/tdbus_ip?bid={bid}&net_tag=all".format(
            tdbus_manager_host  =   tdbus_manager_host,
            bid                 =   bid
        )


    @property
    def address(self):
        """
        从tdbus集群中随机选取一个服务器进行数据上传
        :return:
        """
        if time.time() - self.last_update > SERVER_IP_FRESH_INTERVAL or self.server_addr is None:
            cluster_servers = HttpClient.get(self.manager_address, json_ret=True)
            server_port = 8000
            hosts       = cluster_servers["host"]
            random_host = random.choice([value for key, value in list(hosts.items())])
            self.last_update = time.time()
            self.server_addr = "{host}:{port}".format(host = random_host, port = server_port)
        return self.server_addr


    def send(self, message):
        """
        请求消息
        :param message:
        :return:
        """
        result = HttpClient.get("http://{host}/tdbus/common".format(host = self.address), message, content_type="application/x-www-form-urlencoded", json_ret=True)
        if int(result["code"]) != 1:
            raise Exception("send msg failed, %s" % result["msg"])


class TdbankHttpMessageList(object):
    """
    tdbank http接入类型消息（多条）
    bid=business_id&tid=interface_id&dt=1358214251563&cnt=2&body=content1;content2;content3;content4;content5\ncontent1;content2;content3;content4;content5
    """

    def __init__(self, bid, tid, client, sep = "\t", send_batch = 50, type = "json"):
        """

        :param bid:
        :param tid:
        """
        self.bid        = bid
        self.tid        = tid
        self.cnt        = 0
        self.sep        = sep
        self.client     = client
        self.send_batch = send_batch
        self.lst_msg    = []
        self.type       = type


    def add(self, message):
        """
        添加消息
        :param message:
        :return:
        """
        #先把缓存的消息批量发出去
        if self.cnt >= 50:
            self.__send()
            #重置状态
            self.cnt = 0
            self.lst_msg = []
        #把消息加入缓存
        if message.bid != self.bid and message.tid != self.tid:
            raise Exception("bid or tid are not the same")
        self.lst_msg.append(message)
        self.cnt += 1


    def __send(self):
        """
        发送消息
        :return:
        """
        message = self.__form_msgs()
        self.client.send(message)


    def flush(self):
        """
        最后记得flush一下，把内存中的数据都发出去
        :return:
        """
        #发送消息
        message = self.__form_msgs()
        self.client.send(message)
        # 重置状态
        self.cnt = 0
        self.lst_msg = []


    def __form_msgs(self):
        """
        组织消息格式
        :return:
        """
        return {
            "bid"   :   self.bid,
            "tid"   :   self.tid,
            "cnt"   :   self.cnt,
            "dt"    :   int(round(time.time() * 1000)),
            "body"  :   self.__get_body()
        }

    def __get_body(self):
        """

        :return:
        """
        if self.type == "json":
            return quote(json.dumps(self.lst_msg))
        elif self.type == "tdw":
            return quote("\n".join([self.sep.join([str(item) for item in item_msg]) for item_msg in self.lst_msg]))
        else:
            raise Exception("msg type not defined")



class TdbankHttpMessage(dict):
    """
    单条tube消息
    """

    def __init__(self, bid, tid, data, client = None, sep = "\t", type = "json"):
        """

        :param bid:
        :param tid:
        :param data:
        :param client:
        :param sep:
        :param type: 发送的数据格式，默认为json格式，如果为tdw，才采用\t分割字段
        """
        self.bid    = bid
        self.tid    = tid
        self.dt     = 0
        self.sep    = sep
        self.type   = type
        self.client = client
        dict.__init__(self, **data)


    def send(self):
        """
        发送数据
        :return:
        """
        if self.client is None:
            raise Exception("you need init the client first")
        #发送消息
        message = self.__form_msgs()
        self.client.send(message)


    def __form_msgs(self):
        """
        组织消息格式
        :return:
        """
        return {
            "bid"   :   self.bid,
            "tid"   :   self.tid,
            "dt"    :   int(round(time.time() * 1000)),
            "body"  :   self.__get_body()
        }


    def __get_body(self):
        """

        :return:
        """
        if self.type == "json":
            return quote(json.dumps(self))
        elif self.type == "tdw":
            return quote(self.sep.join([str(item) for item in self]))
        else:
            raise Exception("msg type not defined")


def test():
    """
    测试
    :return:
    """
    bid = "b_wxg_weixin_pay_oceanus_http"
    tid = "t_wxpay_tdw_pool_usage_realtime"
    #网络客户端
    client = TdbankHttpClient(bid)
    #消息列表
    msg_list = TdbankHttpMessageList(bid, tid, client)
    for i in range(0, 1000):
        msg_list.add(TdbankHttpMessage(bid, tid, ["msg1", "msg2", "msg3", i]))
    #最后记得flush一下
    msg_list.flush()

