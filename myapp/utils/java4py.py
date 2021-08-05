# -*- coding:utf-8 -*-
"""
des: 
create time: 
version: 
"""

import os
import sys
import jpype
import threading
from src.utils.log import Log
from src.utils.config import Config

_SEP = os.path.pathsep
if sys.platform == 'cygwin':
    _SEP = ';'

class Java4py(object):
    """
    调用java
    注意！！！！千万不能在主进程中启动jvm，又在子进程中复用，否则会卡住
    """


    def __init__(self, jars, *args, **kwargs):
        """

        :param jars: jar文件路径，可以用list传递多个
        :param args:
        :param kwargs:
        """
        if isinstance(jars, list):
            #多个jar用":"号隔开
            self.jar_path = jars
        elif isinstance(jars, str):
            self.jar_path = [jars]
        else:
            raise Exception("jar path must ends with '.jar'")
        self.args = args
        self.kwargs = kwargs
        self.stdout = kwargs.get("stdout", "dev/null")
        self.stderr = kwargs.get("stderr", "dev/null")
        self.auto_shutdown = kwargs.get("auto_shutdown", False)


    def __enter__(self):
        """
        启动jvm
        :return:
        """
        class_path_dir = "{tools}/class_path".format(tools = Config.tools_dir)
        if os.path.exists(class_path_dir) is False:
            os.mkdir(class_path_dir)
        #建立软链接
        for jar in self.jar_path:
            self.__check_jar(jar)
            jar_link_dst = "{dir}/{file_name}".format(
                dir = class_path_dir,
                file_name = os.path.basename(jar)
            )
            if os.path.exists(jar_link_dst) is False:
                try:
                    #删除软链接
                    os.readlink(jar_link_dst)
                    #没报错，说明软链接存在，则先删除
                    os.remove(jar_link_dst)
                except:
                    pass
                os.symlink(jar, jar_link_dst)
        #启动jvm
        self.__start_jvm(class_path_dir)
        #多线程兼容
        if not jpype.isThreadAttachedToJVM():
            jpype.attachThreadToJVM()
            Log.debug("attached to existed jvm")


    def __start_jvm(self, class_path_dir):
        """

        :return:
        """
        if not jpype.isJVMStarted():
            jpype.addClassPath("%s/*" % class_path_dir.rstrip("/"))
            jpype.startJVM(jpype.getDefaultJVMPath(), *tuple(self.args), convertStrings=True)
            Log.debug("[pid-%s tid:%s]jvm started with class_path %s" % (
                os.getpid(),
                threading.currentThread().ident,
                jpype.getClassPath()
            ))
        # else:
        #     Log.debug("[pid-%s tid:%s]jvm already started with class_path %s" % (
        #         os.getpid(),
        #         threading.currentThread().ident,
        #         jpype.getClassPath()
        #     ))
        try:
            #重定向标准输出和标准错误
            jpype.java.lang.System.setOut(
                jpype.java.io.PrintStream(jpype.java.io.File(self.stdout)))  # NUL for windows, /dev/null for unix
            jpype.java.lang.System.setErr(
                jpype.java.io.PrintStream(jpype.java.io.File(self.stderr)))  # NUL for windows, /dev/null for unix
        except Exception as ex:
            pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        """

        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        #不用每次用完之后就关闭，以方便下次复用
        if self.auto_shutdown and jpype.isJVMStarted():
            jpype.shutdownJVM()


    @staticmethod
    def shutdown():
        """

        :return:
        """
        if jpype.isJVMStarted(): jpype.shutdownJVM()


    def __check_jar(self, path):
        """

        :param path:
        :return:
        """
        if path.endswith(".jar") is False:
            raise Exception("jar path must ends as .jar")
        return path

