# -*- coding:utf-8 -*-
"""
des: 
create time: 
version: 
"""

import os
import sys
import jpype

_SEP = os.path.pathsep
if sys.platform == 'cygwin':
    _SEP = ';'

class Java(object):
    """
    调用java
    """

    def __init__(self, jars, auto_shutdown = False, *args, **kwargs):
        """

        :param jars: jar文件路径，可以用list传递多个
        :param args:
        :param kwargs:
        """
        if isinstance(jars, list):
            #多个jar用":"号隔开
            self.jars = _SEP.join([self.__check_jar(jar) for jar in jars])
        elif isinstance(jars, str):
            self.__check_jar(jars)
            self.jars = jars
        else:
            raise Exception("jar path must ends with '.jar'")
        self.args = args
        self.kwargs = kwargs
        self.auto_shutdown = auto_shutdown


    def __enter__(self):
        """
        启动jvm
        :return:
        """
        if not jpype.isJVMStarted():
            args = ['-Djava.class.path=%s' % self.jars, "-ea"]
            args.extend(self.args)
            jpype.startJVM(jpype.getDefaultJVMPath(), *tuple(args), convertStrings=True)
        else:
            class_path = set(jpype.getClassPath().split(_SEP))
            for jar in self.jars.split(_SEP):
                if jar not in class_path:
                    jpype.addClassPath(jar)
        if not jpype.isThreadAttachedToJVM():
            jpype.attachThreadToJVM()


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



if __name__ == '__main__':
    with Java(jars=["/data/home/xxx/tdw_auth_client.jar", "/data/home/xxx.jar"]) as java:
        TdwAuthClientClass = jpype.JClass("com.tencent.tdw.TdwAuthClient")
        TdwAuthClientClass.setServiceUrl("http://auth.tdw.oa.com")