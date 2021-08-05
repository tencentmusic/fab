# -*- coding:utf-8 -*-
"""
des: tdw鉴权客户端
create time: 2020年04月09日
version: xiadu
"""
import requests
import base64
import json
import time
from Crypto.Cipher import DES3
from Crypto.Util.Padding import pad, unpad


class TdwTauthAuthentication(object):
    request_url = "http://auth.tdw.oa.com/api/auth/st2"

    def __init__(self, user_name, cmk_key, target="Common-Scheduler", proxy_user=None):
        self.user_name = user_name  # cmk认证文件的用户名
        self.cmk_key = base64.b64decode(cmk_key).decode('hex')
        assert len(self.cmk_key) == 24  # 秘钥长度24,DES3-ECB模式
        self.target = target
        self.proxy_user = proxy_user

        self.decryptor = DES3.new(self.cmk_key, DES3.MODE_ECB)  # DES3.ECB 解密器
        self.encryptor = None  # DES3.ECB 加密器,需要用session_key构造
        self.service_ticket = None
        self.expire_time_stamp = None

    def get_authentication_header(self):
        if not self.service_ticket or self.expire_time_stamp <= int(time.time()) * 1000:
            # 1.请求鉴权信息
            identifier = {
                "user": self.user_name,
                "host": "127.0.0.1",
                "target": self.target,
                "lifetime": 7200000,
                "timestamp": int(time.time())
            }
            identifier_body = base64.b64encode(json.dumps(identifier))
            # 2.获取session ticket
            response = requests.get(self.request_url, params={"ident": identifier_body})
            session_ticket = response.json()

            # 保存服务端ticket
            self.service_ticket = session_ticket["st"]

            # 3.三步-解密客户端ticket
            client_ticket = base64.b64decode(session_ticket["ct"])
            client_ticket = unpad(self.decryptor.decrypt(client_ticket), DES3.block_size)
            client_ticket = json.loads(client_ticket)

            # 4.获取session_key,生成加密器
            session_key = base64.b64decode(client_ticket['sessionKey'])
            self.encryptor = DES3.new(session_key, DES3.MODE_ECB)
            # 5.更新过期时间
            self.expire_time_stamp = client_ticket["timestamp"] + client_ticket["lifetime"]

        # 构造请求客户端鉴权请求头
        client_authenticator = {
            "principle": self.user_name,
            "host": "127.0.0.1",
            "timestamp": int(time.time()) * 1000
        }
        if self.proxy_user:
            client_authenticator["proxyUser"] = self.proxy_user
        # 三步-加密鉴权信息
        client_authenticator = json.dumps(client_authenticator)
        client_authenticator = self.encryptor.encrypt(pad(client_authenticator, DES3.block_size))
        client_authenticator = base64.b64encode(client_authenticator)

        # 拼接鉴权信息
        authentication = "tauth.{}.{}".format(self.service_ticket, client_authenticator)

        return {"secure-authentication": authentication}
