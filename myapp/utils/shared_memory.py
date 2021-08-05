# -*- coding:utf-8 -*-
"""
des: 
create time: 
version: 
"""

import sys
import time
from posix_ipc import SharedMemory as _SHM, ExistentialError, O_CREAT
from mmap import mmap


class SharedMemory(object):
    """
    共享内存组件
    """
    ENDING_CHAR = b"\0"

    def __init__(self, name, size = 0):
        """
        初始化
        :param args:
        :param kwargs:
        """
        self.name = name if name.startswith("/") else "/" + name
        self.size = size


    def read(self):
        """
        读取数据
        :return:
        """
        shm = _SHM(self.name)
        mp = mmap(shm.fd, shm.size)
        shm.close_fd()
        mp.seek(0)
        letters = []
        letter = mp.read_byte()
        while letter != 0:
            letters.append(letter)
            letter = mp.read_byte()
        return "".join([chr(letter) for letter in letters])


    def write(self, data):
        """
        向共享内存中写入数据
        :param data:
        :return:
        """
        if isinstance(data, str):
            data = data.encode()
        if not isinstance(data, bytes):
            raise Exception("write data must be bytes type")
        data = data + SharedMemory.ENDING_CHAR
        try:
            shm = _SHM(self.name)
        except ExistentialError:
            shm = _SHM(self.name, flags = O_CREAT, size = self.size)
            print("created new shared memory")
        mp = mmap(shm.fd, shm.size)
        shm.close_fd()
        mp.seek(0)
        mp.write(data)


def write(name, size):
    """

    :param name:
    :param size:
    :return:
    """
    index = 0
    while 1:
        shm = SharedMemory(name, size=size)
        shm.write("my name is jeffwan, index=%s" % index)
        index += 1
        time.sleep(1)

def read(name, size):
    """

    :param name:
    :param size:
    :return:
    """
    while 1:
        shm = SharedMemory(name, size=size)
        print(shm.read())
        time.sleep(1)


if __name__ == '__main__':
    name = "/test_shared_memory"
    size = 1024

    cmd = sys.argv[1]

    if cmd == "read":
        read(name, size)
    elif cmd == "write":
        write(name, size)
    else:
        print("cmd {cmd} not found")
