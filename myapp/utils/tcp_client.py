#  -*- coding: utf-8 -*-

#############################################
#
#    TCP客户端
#
#############################################


import socket
import time

try:
    import json
except:
    # python 2.4
    import simplejson as json

_ONCE_GET_DATA_SIZE = 2 * 1024 * 1024
_DEFAULT_TIMEOUT = 60
_RECV_PACKET_LENGTH_SIZE = 8


class TcpClient(object):
    """
       提供给其他系统对接接口使用
    """

    def __init__(self, ip, port):
        """
        初始化
        :param ip:
        :param port:
        """
        self.server_ip = ip
        self.server_port = port
        self.error = ""
        # 初始化
        self.__init_value()


    def get_server_ip(self):
        """
        获取ip
        :return:
        """
        return self.server_ip


    def get_server_port(self):
        """

        :return:
        """
        return self.server_port


    def __init_value(self):
        """

        :return:
        """
        pass


    def get_last_error(self):
        """

        :return:
        """
        return self.error


    def get_server_addr(self):
        """

        :return:
        """
        return "%s:%d" % (self.server_ip, self.server_port)


    def __connect(self):
        """

        :return:
        """
        skt = None
        try:
            skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            skt.settimeout(_DEFAULT_TIMEOUT)
            skt.connect((self.server_ip, self.server_port))
        except:
            skt = None
        return skt


    def __sendall(self, socket, data, tiemout):
        """
        发送数据
        :param socket:
        :param data:
        :param tiemout:
        :return:
        """
        if socket is None:
            self.error = "socket is none"
            return False

        if data is None or len(data) < 1:
            self.error = "data is null"
            return False

        if tiemout is None:
            self.error = "timeout is none"
            return False

        start_time = int(time.time())
        amount = len(data)
        count = 0
        while (count < amount):
            v = -1
            try:
                v = socket.send(data[count:])
            except:
                pass

            if int(time.time()) - start_time >= tiemout:
                self.error = "send data timeout"
                break

            if v <= 0:
                time.sleep(0.1)
                continue
            count += v

        return count >= amount


    def __recv(self, socket, timeout, packet_size=_ONCE_GET_DATA_SIZE):
        """
        funciton name:__recvData
        des: 接收server返回信息
        input: nPacketSizeLen 返回包长度的大小， None说明没有大小
        output:
        """
        recv_data_len = None
        start_time = int(time.time())
        cur_size = 0
        info = ""
        while True:
            try:
                data = socket.recv(packet_size)
            except Exception as ex:
                self.error = "recv data error. [%s]" % str(ex)
                data = None

            if data is None:
                break
            cur_len = len(data)
            info = info + data
            cur_size += cur_len

            # 没有指定包长度
            if packet_size is None:
                if cur_len > 0:
                    try:
                        json.loads(info)
                        # 包能解析正常
                        break
                    except:
                        pass
            else:
                # 指定包长度为nPacketSizeLen
                if recv_data_len is None \
                    and cur_size >= packet_size:
                    try:
                        recv_data_len = int(info[:packet_size])
                    except:
                        break
                    info = info[packet_size:]
                    cur_size -= packet_size

                if recv_data_len is not None \
                    and cur_size >= recv_data_len:
                    break
            if int(time.time()) - start_time >= timeout:
                self.error = "recv data timeout"
                break
        if info is None:
            raise Exception(self.error)
        return info


    def send_data(self, data, timeout=_DEFAULT_TIMEOUT):
        """
        发送数据并负责接收对应的包数据
        :param data:
        :param timeout:
        :return:
        """
        if data is None:
            self.error = "data is none"
            return None

        socket = self.__connect()
        if socket is None:
            self.error = "connect server failed"
            return None
        try:
            socket.settimeout(timeout)
            info = None
            # objSocket.sendall(strData)
            # 替换内部函数 objSocket.sendall(strData), timeout内部可能处理不明确
            # 注意退出前一定要socket.close()
            ret = self.__sendall(socket, data, timeout)
            if ret is True:
                info = self.__recv(socket, timeout, 8)
            #强制关闭连接
            socket.shutdown(2)
        except Exception as ex:
            info = None
            self.error = "send data to server failed " + str(ex)
        finally:
            socket.close()
        if not info or info is None:
            raise Exception(self.error)
        return info


    def send_data_recv_pack_size_len(self, data, timeout=_DEFAULT_TIMEOUT, nPacketSizeLen=None):
        """
                    发送数据并负责接收对应的包数据
        """
        if data is None:
            self.error = "data is none"
            return None

        socket = self.__connect()
        if socket is None:
            self.error = "connect server failed"
            return None

        try:
            start = int(time.time())
            socket.settimeout(timeout)
            info = None
            # objSocket.sendall(strData)
            # 替换内部函数 objSocket.sendall(strData), timeout内部可能处理不明确
            # 注意退出前一定要socket.close()
            ret = self.__sendall(socket, data, timeout)
            if ret is True:
                new_timeout = timeout - (int(time.time()) - start)
                info = self.__recv(socket, new_timeout, nPacketSizeLen)

        except Exception as ex:
            info = None
            self.error = "send data to server failed " + str(ex)

        try:
            socket.close()
        except:
            pass

        if not info or info is None:
            raise Exception(self.error)

        return info


if __name__ == '__main__':
    tcp_clent = TcpClient("127.0.0.1", 5000)
    tcp_clent.send_data(json.dumps({}))

