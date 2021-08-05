# -*- coding:utf-8 -*-
"""
des: 
create time: 2015-7-28 
version: 
"""

import re
import os
from src.utils.config import Config
from src.utils.log import Log
from pilot_command.commands import Command


class __HDFS(object):
    """
    hdfs路径
    """
    def __call__(self, hdfs_path):
        """

        :param args:
        :param kwargs:
        :return:
        """
        if hdfs_path.startswith("hdfs://"):
            return hdfs_path
        hdfs_host = Config.hdfs["host"]
        host =  "hdfs://{host}{path}".format(host = hdfs_host, path = hdfs_path)
        return host

HDFS = __HDFS()




class _HDFSActionBase(object):
    """
    HDFS操作基类
    """
    CMD_TYPE_FS     =   "fs"
    CMD_TYPE_ADMIN  =   "dfsadmin"


    def __init__(self, hdfs_path = None, cmd_type = CMD_TYPE_FS):
        """

        :param objHdfsPath:
        """
        self.hdfs_path    =   hdfs_path
        self.cmd_type     =   cmd_type
        self.auth_info = "-Dhadoop.job.ugi={user}:{passwd},users".format(
            user = Config.hdfs["user"],
            passwd = Config.hdfs["passwd"]
        )


    def do(self):
        """

        :return:
        """
        hadoop_command = self.create_command()
        Log.debug("execute hadoop command:%s" % hadoop_command)
        return self.parse(self.execute(hadoop_command))


    def execute(self, cmd):
        """

        :param cmd:
        :return:
        """
        stdout = Command.execute(cmd)
        if stdout.find("Namenode trash configuration") != -1:
            raise Exception(stdout.strip())
        return stdout.strip()


class _FileStat(dict):
    """
    文件/目录基本信息
    """

    def __init__(self, file_info):
        """

        :param file_info:
        """
        user_priv, group_priv, owner, group, size_byte, modify_time, file_path = file_info
        dict.__init__(self, user_priv   = user_priv,
                      group_priv  = group_priv,
                      owner       = owner,
                      group       = group,
                      size        = size_byte,
                      modify_time = modify_time,
                      file_path   = file_info)

    @property
    def path(self):
        """

        :return:
        """
        return self["file_path"]


    @property
    def size(self):
        """

        :return:
        """
        return self["size"]


    @property
    def time(self):
        """

        :return:
        """
        return self["modify_time"]



class _LsAction(_HDFSActionBase):
    """
    列表当前路径下的所有文件和目录
    """

    def __init__(self, hdfs_path):
        """

        :param objHdfsPath:
        """
        _HDFSActionBase.__init__(self, hdfs_path)


    def create_command(self):
        """

        :return:
        """
        return """hadoop {cmd_type} {auth} -ls {path}""".format(cmd_type = self.cmd_type, auth = self.auth_info, path = self.hdfs_path)



    def parse(self, std_out):
        """

        :return:
        Found 3 items
        drwxrwxrwx   - tdwadmin usergroup          0 2018-11-20 23:58 hdfs://ss-teg-3-v2/stage/outface/teg/u_teg_sec_unifiedstorage/min_out/20181120
        drwxrwxrwx   - tdwadmin usergroup          0 2018-11-22 00:01 hdfs://ss-teg-3-v2/stage/outface/teg/u_teg_sec_unifiedstorage/min_out/20181121
        drwxrwxrwx   - tdwadmin usergroup          0 2018-11-22 15:15 hdfs://ss-teg-3-v2/stage/outface/teg/u_teg_sec_unifiedstorage/min_out/20181122
        """
        finds = re.findall(self.get_pattern(), std_out)
        return [_FileStat(item_file_info) for item_file_info in finds]


    def get_pattern(self):
        """

        :return:
        """
        return r"""([a-z-_]+)\s+([a-z-_]+)\s+([a-z-_]+)\s+([a-z-_]+)\s+([0-9]+)\s+([0-9]{4}\-[0-9]{2}\-[0-9]{2}\s[0-9]{2}:[0-9]{2})\s+(hdfs://[a-zA-Z0-9_/\-]+)"""


class _LsDirAction(_HDFSActionBase):
    """
    列表当前路径下的所有文件和目录
    """

    def __init__(self, hdfs_path):
        """

        :param objHdfsPath:
        """
        _HDFSActionBase.__init__(self, hdfs_path)


    def create_command(self):
        """

        :return:
        """
        return """hadoop {cmd_type} {auth} -ls {path}""".format(cmd_type = self.cmd_type, auth = self.auth_info, path = self.hdfs_path)



    def parse(self, stdout):
        """

        :return:
        Found 3 items
        drwxrwxrwx   - tdwadmin usergroup          0 2018-11-20 23:58 hdfs://ss-teg-3-v2/stage/outface/teg/u_teg_sec_unifiedstorage/min_out/20181120
        drwxrwxrwx   - tdwadmin usergroup          0 2018-11-22 00:01 hdfs://ss-teg-3-v2/stage/outface/teg/u_teg_sec_unifiedstorage/min_out/20181121
        drwxrwxrwx   - tdwadmin usergroup          0 2018-11-22 15:15 hdfs://ss-teg-3-v2/stage/outface/teg/u_teg_sec_unifiedstorage/min_out/20181122
        """
        finds = re.findall(self.get_pattern(), stdout)
        return finds


    def get_pattern(self):
        """

        :return:
        """
        # return r"""([a-z-_]+)\s+([a-z-_]+)\s+([a-z-_]+)\s+([a-z-_]+)\s+([0-9]+)\s+([0-9]{4}\-[0-9]{2}\-[0-9]{2}\s[0-9]{2}:[0-9]{2})\s+(hdfs://[a-zA-Z0-9_/\-]+)"""
        return r"""hdfs://[a-zA-Z0-9_/\-.0-9]+"""


class _WcDirAction(_HDFSActionBase):
    """
    列表当前路径下的所有文件和目录的行数
    """

    def __init__(self, hdfs_path):
        """

        :param objHdfsPath:
        """
        _HDFSActionBase.__init__(self, hdfs_path)


    def create_command(self):
        """

        :return:
        """
        return """hadoop {cmd_type} {auth} -cat {path}/*|wc -l""".format(cmd_type = self.cmd_type, auth = self.auth_info, path = self.hdfs_path)



    def parse(self, stdout):
        """

        :param stdout:
        :return:
        """
        return stdout



class _DusDirAction(_HDFSActionBase):
    """
    列表当前路径下的所有文件的大小
    """

    def __init__(self, hdfs):
        """

        :param objHdfsPath:
        """
        _HDFSActionBase.__init__(self, hdfs)


    def create_command(self):
        """

        :return:
        """
        return """hadoop {cmd_type} {auth} -du -s {path}|awk '{print $1}'""".format(cmd_type = self.cmd_type, auth = self.auth_info, path = self.hdfs_path)


    def parse(self, stdout):
        """

        :param stdout:
        :return:
        """
        if stdout.isdigit():
            return int(stdout)
        raise Exception(stdout)


class _DuAction(_HDFSActionBase):
    """
    获取当前目录的文件大小
    """

    def __init__(self, hdfs_path):
        """

        :param objHdfsPath:
        """
        _HDFSActionBase.__init__(self, hdfs_path)


    def create_command(self):
        """

        :return:
        """
        return """hadoop {cmd_type} {auth} -du -s {path}""".format(cmd_type = self.cmd_type, auth = self.auth_info, path = self.hdfs_path)



    def parse(self, stdout):
        """

        :param stdout:
        :return:
        """
        lst_data = stdout.split(" ")
        if len(lst_data) == 0:
            raise Exception("get size of hdfs failed:%s" % stdout)
        if lst_data[0].isdigit() is False:
            raise Exception("get size of hdfs failed:%s" % stdout)
        return int(lst_data[0])



class _MkDirAction(_HDFSActionBase):
    """
    创建目录操作
    """

    def __init__(self, hdfs_path):
        """

        :param objHdfsPath:
        """
        _HDFSActionBase.__init__(self, hdfs_path)


    def create_command(self):
        """

        :return:
        """
        return """hadoop {cmd_type} {auth} -mkdir {path}""".format(cmd_type = self.cmd_type, auth = self.auth_info, path = self.hdfs_path)



    def parse(self, stdout):
        """

        :return:
        Found 3 items
        drwxrwxrwx   - tdwadmin usergroup          0 2018-11-20 23:58 hdfs://ss-teg-3-v2/stage/outface/teg/u_teg_sec_unifiedstorage/min_out/20181120
        drwxrwxrwx   - tdwadmin usergroup          0 2018-11-22 00:01 hdfs://ss-teg-3-v2/stage/outface/teg/u_teg_sec_unifiedstorage/min_out/20181121
        drwxrwxrwx   - tdwadmin usergroup          0 2018-11-22 15:15 hdfs://ss-teg-3-v2/stage/outface/teg/u_teg_sec_unifiedstorage/min_out/20181122
        """
        return True


class _RmAction(_HDFSActionBase):
    """
    删除操作
    """

    def __init__(self, hdfs_path, skip_trash = False, force = True):
        """

        :param objHdfsPath:
        """
        self.trash_option = "" if skip_trash is False else "-skipTrash"
        self.force = force
        _HDFSActionBase.__init__(self, hdfs_path)


    def create_command(self):
        """

        :return:
        """
        return """hadoop {cmd_type} {auth} -rm {force} {trash_opition} {path}""".format(cmd_type = self.cmd_type, auth = self.auth_info,
                                                                                        path = self.hdfs_path,
                                                                                        trash_opition = self.trash_option,
                                                                                        force = "-r" if self.force else ''
                                                                                        )


    def parse(self, stdout):
        """

        :return:
        Found 3 items
        drwxrwxrwx   - tdwadmin usergroup          0 2018-11-20 23:58 hdfs://ss-teg-3-v2/stage/outface/teg/u_teg_sec_unifiedstorage/min_out/20181120
        drwxrwxrwx   - tdwadmin usergroup          0 2018-11-22 00:01 hdfs://ss-teg-3-v2/stage/outface/teg/u_teg_sec_unifiedstorage/min_out/20181121
        drwxrwxrwx   - tdwadmin usergroup          0 2018-11-22 15:15 hdfs://ss-teg-3-v2/stage/outface/teg/u_teg_sec_unifiedstorage/min_out/20181122
        """
        if len(stdout.strip()) != 0:
            Log.debug(stdout.strip())
        return True


class _GetAction(_HDFSActionBase):
    """
    下载文件
    """

    def __init__(self, hdfs_path, local_path):
        """

        :param objHdfsPath:
        """
        self.local_path   =   local_path
        self.hdfs_path    =   hdfs_path
        if os.path.isdir(local_path) is False:
            raise Exception("local path %s is not a dir" % local_path)
        _HDFSActionBase.__init__(self, hdfs_path)


    def create_command(self):
        """

        :return:
        """
        return """hadoop {cmd_type} {auth} -get {path} {local_path}""".format(cmd_type      = self.cmd_type,
                                                                              auth          = self.auth_info,
                                                                              path          = self.hdfs_path,
                                                                              local_path    = self.local_path)


    def parse(self, stdout):
        """

        :param stdout:
        :return:
        """
        file_name = self.hdfs_path.split("/")[-1]
        local_file = self.local_path.rstrip("/") + "/" + file_name.lstrip("/")
        if os.path.exists(local_file) is False:
            raise Exception("downloaded file %s not found in local disk" % local_file)
        return True



class _PutAction(_HDFSActionBase):
    """
    上传本地文件到HDFS
    """
    def __init__(self, local_file_path, hdfs_path):
        """

        :param objHdfsPath:
        """
        if not isinstance(local_file_path, str):
            raise Exception("file path must be string type, not %s" % type(local_file_path))
        if os.path.exists(local_file_path) is False:
            raise Exception("local file %s not exists" % local_file_path)
        self.local_file_path   =   local_file_path
        _HDFSActionBase.__init__(self, hdfs_path)


    def create_command(self):
        """

        :return:
        """
        return """hadoop {cmd_type} {auth} -put {local_path} {path}""".format(cmd_type      = self.cmd_type,
                                                                              auth          = self.auth_info,
                                                                              path          = self.hdfs_path,
                                                                              local_path    = self.local_file_path)


    def parse(self, stdout):
        """

        :param stdout:
        :return:
        """
        return True


class _ChmodAction(_HDFSActionBase):
    """
    授权动作
    """

    def __init__(self, hdfs_path, acl_code):
        """

        :param strLocalFilePath:
        :param acl_code:
        """
        self.acl_code =   acl_code
        _HDFSActionBase.__init__(self, hdfs_path)


    def create_command(self):
        """

        :return:
        """
        return """hadoop {cmd_type} {auth} -chmod -R {acl_code} {path}""".format(cmd_type      = self.cmd_type,
                                                                                 auth          = self.auth_info,
                                                                                 path          = self.hdfs_path,
                                                                                 acl_code      = self.acl_code)

    def parse(self, stdout):
        """

        :param stdout:
        :return:
        """
        return True



class _CheckExistAction(_HDFSActionBase):
    """

    """

    def __init__(self, hdfs_path):
        """

        :param objHdfsPath:
        """
        _HDFSActionBase.__init__(self, hdfs_path)


    def do(self):
        """

        :return:
        """
        hadoop_command = self.create_command()
        Log.debug("execute hadoop command:%s" % hadoop_command)
        return self.parse(self.execute(hadoop_command))


    def create_command(self):
        """

        :return:
        """
        return """hadoop {cmd_type} {auth} -test -e {path};echo $?""".format(cmd_type      = self.cmd_type,
                                                                             auth          = self.auth_info,
                                                                             path          = self.hdfs_path)


    def parse(self, stdout):
        """

        :param stdout:
        :return:
        """
        if not stdout:
            return False
        ret_code = int(stdout.strip())
        return True if ret_code == 0 else False


class HDFSHandler(object):
    """
    HDFS操作API
    hadoop客户端安装方法：http://km.oa.com/group/bigdatadoc/articles/show/299501
    """

    @staticmethod
    def exist(hdfs):
        """

        :param hdfs:
        :return:
        """
        return _CheckExistAction(hdfs).do()


    @staticmethod
    def ls(hdfs):
        """

        :param strFilePath:
        :return:
        """
        return _LsAction(hdfs).do()


    @staticmethod
    def mkdir(hdfs, overwrite = False):
        """
        创建目录
        :param hdfs:
        :param overwrite: 如果目录已存在，则先删除目录
        :return:
        """
        if HDFSHandler.exist(hdfs) is True:
            if overwrite is True:
                HDFSHandler.rmr(hdfs)
                _MkDirAction(hdfs).do()
            else:
                return
        else:
            _MkDirAction(hdfs).do()


    @staticmethod
    def rm(hdfs, skip_trash= True, force = False):
        """
        删除（移动到垃圾箱）
        :param hdfs:
        :return:
        """
        _RmAction(hdfs, skip_trash= skip_trash, force=force).do()


    @staticmethod
    def rmr(hdfs, skip_trash= True):
        """
        永久删除
        :param hdfs:
        :return:
        """
        _RmAction(hdfs, skip_trash= True, force=True).do()


    @staticmethod
    def get(hdfs, local_path):
        """
        下载文件到本地
        :param hdfs:
        :param local_path:
        :return:
        """
        _GetAction(hdfs, local_path).do()


    @staticmethod
    def put(local_path, hdfs):
        """
        上传本地文件
        :param local_path:
        :param hdfs:
        :return:
        """
        _PutAction(local_path, hdfs).do()


    @staticmethod
    def chmod(hdfs, acl_mode):
        """
        目录授权
        :param hdfs:
        :param acl_mode:权限控制，例如755， 777
        :return:
        """
        _ChmodAction(hdfs, acl_mode).do()

    @staticmethod
    def ls_dir(hdfs):
        """
        查看目录下的文件信息
        :param hdfs:
        :param strAclCode:
        :return:
        """
        return _LsDirAction(hdfs).do()
    
    @staticmethod
    def wcl(hdfs):
        """
        统计目录下的所有文件行数, 不适合大文件
        :param hdfs:
        :return:
        """
        return _WcDirAction(hdfs).do()


    @staticmethod
    def dus(hdfs):
        """
        计算目录下的文件大小
        :param hdfs:
        :return:
        """
        return _DusDirAction(hdfs).do()




if __name__ == '__main__':
    # print "mkdir---------------"
    from src.utils.hdfs_handler import HDFSHandler
    print(HDFSHandler.mkdir(HDFS("model_storage")))
    # print HDFSHandler.mkdir(HDFS("model_storage"))
    # print "ls---------------"
    # print HDFSHandler.ls(HDFS())
    # print "rmr---------------"
    # print HDFSHandler.rm(HDFS("model_storage"))
    # print "ls---------------"
    # print HDFSHandler.ls(HDFS())
    # print HDFSHandler.put("/tmp/test.model", HDFS("model_storage"))
    # print [item.path for item in HDFSHandler.ls(HDFS())]
    # print HDFSHandler.get(HDFS("model_storage", "test.model"), "/tmp/model")