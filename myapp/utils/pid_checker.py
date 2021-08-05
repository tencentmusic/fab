# -*- coding:utf-8 -*-
"""
des: 
create time: 2018-7-28 
version: 
"""

import os
from src.utils.log import Log
from src.utils.config import Config
from src.utils.commands import Command


class PidChecker(object):


    def __init__(self, process_name):
        """

        :param process_name:
        """
        data_dir          = Config.data_dir
        self.process_name =   process_name
        pid_dir           = data_dir.rstrip("/") + "/pids"
        if os.path.exists(pid_dir) is False:
            os.mkdir(pid_dir)
        self.pid_name = pid_dir + "/" + process_name


    def write_pid(self):
        """

        :return:
        """
        if os.path.exists(self.pid_name) is True:
            raise Exception("process %s already exists!" % self.process_name)
        with open(self.pid_name, "w") as objFile:
            objFile.write(str(os.getpid()))
        return self


    def get_pid(self):
        """

        :return:
        """
        strPid = None
        with open(self.pid_name, "r") as objFile:
            strPid = objFile.read(os.getpid()).strip()
        return strPid


    def check_executed(self):
        """
        检查进程是否已经执行过
        :return:
        """
        if os.path.exists(self.pid_name) is not True:
            return False
        return True


    def clean(self):
        """

        :return:
        """
        if os.path.exists(self.pid_name) is True:
            os.remove(self.pid_name)

