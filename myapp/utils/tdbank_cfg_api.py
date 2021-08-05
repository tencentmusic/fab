# -*- coding:utf-8 -*-
"""
des: 封装TDBANK配置中心管理接口
create time: 2015-7-28 
version: 
"""
import time
import json
import urllib.request, urllib.error, urllib.parse
import traceback

from src.utils.log import Log

IP = "10.213.2.4"
PORT = 8099
# 必填，校验是否管理员或者负责人
OPERATOR = "uniquewang"

RETRY_NUM = 3
RETRY_INTERVAL = 1
TIMEOUT = 60
BUS_ID = "b_teg_sec_unifiedstorage_anping_instore_network"
FIELD_TYPES = ("bigint", "double", "string")


class NetConn(object):
    """支持失败重试的网络请求"""

    def __init__(self, strUrl, strParams=None):
        """

        :param strUrl:
        :param objParams:

        """
        self.strUrl = strUrl
        self.strParams = strParams
        self.strError = ""

    def request(self):
        """
        请求
        :return:
        """
        iExeNum = 0
        bRet = True
        dictResult = None
        while iExeNum <= RETRY_NUM:
            try:
                objUrl = urllib.request.urlopen(self.strUrl, data=self.strParams, timeout=TIMEOUT)
                # {"returnStr":"OK, tdw api ret:{\"code\":\"0\",\"message\":\"successfully\"}","state":"0"}
                strData = objUrl.read()
                dictResult = json.loads(strData)
                if dictResult["state"] != "0":
                    self.strError = dictResult["returnStr"]
                    bRet = False
                bRet = True
                self.strError = ""
            except Exception as ex:
                self.strError = traceback.format_exc()
                bRet = False
            print(("[url:%s][params:%s][ret:%s][err:%s]" % (self.strUrl, self.strParams, bRet, self.strError)))
            iExeNum += 1
            if bRet is True:
                break
        if bRet is False:
            return None
        return dictResult

    def getLastError(self):
        """

        :return:
        """
        return self.strError


class FieldToAdd(dict):
    """
    需要添加的字段
    """

    def __init__(self, strFieldName, strFieldType):
        """

        :param strFieldName:
        :param strFieldType:
        """
        if strFieldType not in FIELD_TYPES:
            raise Exception("field type must be in %s not %s" % (str(FIELD_TYPES), strFieldType))
        dict.__init__(self, op="add", fieldNewName=strFieldName, fieldType=strFieldType)


class FieldToDelete(dict):
    """
    需要删除的字段。实时表冷备表不允许删除。中间表允许删除
    """

    def __init__(self, strFieldName):
        """

        :param strFieldName:
        :param strFieldType:
        """
        dict.__init__(self, op="delete", fieldNewName=strFieldName)


class FieldToModifyType(dict):
    """
    需要修改类型的字段, ocfile格式可改，orcfile格式不可改（实时表冷备表不允许删除。中间表允许删除）
    """

    def __init__(self, strFieldName, strNewFieldType):
        """

        :param strFieldName:
        :param strFieldType:
        """
        if strNewFieldType not in FIELD_TYPES:
            raise Exception("field type must be in %s not %s" % (str(FIELD_TYPES), strNewFieldType))
        dict.__init__(self, op="update_field_type", fieldNewName=strFieldName, fieldType=strNewFieldType)


class FieldToRename(dict):
    """
    需要重命名的字段
    """

    def __init__(self, strOldFieldName, strNewFieldName):
        """

        :param strFieldName:
        :param strFieldType:
        """
        dict.__init__(self, op="update_field_name", fieldNewName=strNewFieldName, fieldOldName=strOldFieldName)


class TdbankFieldsManager(list):
    """
    接口配置中心接口
    示例：curl -d "opid=6&businessid=xxx&interfacename=interface_add_test_robbinli&operator=robbinli&ddls=[{'op':'update_field_name','fieldOldName':'ddd','fieldNewName':'DDD'}]" http:// 10.136.4.90:8099/operator
    """
    # opid=6 变更接口字段（修改字段名，修改字段类型，修改注字段释，新增字段）
    OPID = 6
    URL = "http://%s:%s/operator" % (IP, PORT)

    def __init__(self, strBusId, strInterfaceName):
        """
        初始化
        :param strBusId:
        :param strInterfaceName:
        """
        self.strBusId = strBusId
        self.strError = ""
        self.strInterfaceName = strInterfaceName

    def addField(self, objField):
        """
        添加字段
        :param strFieldName:
        :param strFieldType:
        :return:
        """
        self.append(objField)

    def submit(self):
        """
        提交任务
        :return:
        """
        if len(self) == 0:
            return True
        strParams = self.__getParams()
        objNetConn = NetConn(TdbankFieldsManager.URL, strParams)
        objResult = objNetConn.request()

        if objResult is None:
            self.strError = objNetConn.getLastError()
            return False
        if objResult["state"] != "0":
            self.strError = objResult["returnStr"]
            return False
        return True

    def __getParams(self):
        """
        拼装参数
        :return:
        """
        return "opid={op_id}&businessid={bus}&interfacename={inter_name}&operator={operator}&ddls={ddl}".format(
            op_id=TdbankFieldsManager.OPID,
            bus=self.strBusId,
            inter_name=self.strInterfaceName,
            operator=OPERATOR,
            ddl=json.dumps(self)
        )

    def getLastError(self):
        """

        :return:
        """
        return self.strError


class SourceData(dict):
    """数据源配置项"""
    OPID = 1

    def __init__(self, strIp, strSourcePath, strPreFieldValue=""):
        """

        :param strFieldName:
        :param strFieldType:
        opid=1&ip=0.0.0.0&businessid=b_liaotiao_ylzt&interfacename=FormAlly&datasourcepath=/a/a/a/a&predefinedfieldsvalue=\"daqu=0\"&operator=test
        """
        dict.__init__(self, opid=SourceData.OPID, datasourcepath=strSourcePath,
                      predefinedfieldsvalue=strPreFieldValue, ip=strIp, operator=OPERATOR)

    def getParams(self, strBusId, strInterfaceName):
        """
        获取参数
        :return:
        """
        self["businessid"] = strBusId
        self["interfacename"] = strInterfaceName
        return "&".join(["{key}={value}".format(key=itemKey, value=self[itemKey]) for itemKey in list(self.keys())])

    def getIp(self):
        """
        获取本机IP
        :return:
        """
        return self["ip"]


class TdbankDataSourceMgr(list):
    """
    数据源管理器
    """
    URL = "http://%s:%s/operator" % (IP, PORT)

    def __init__(self, strBusId, strInterfaceName):
        """
        初始化
        :param strBusId:
        :param strInterfaceName:
        """
        self.strBusId = strBusId
        self.strInterfaceName = strInterfaceName
        self.strError = ""

    def addConfig(self, objSourceData):
        """

        :param objSourceData:
        :return:
        """
        self.append(objSourceData)

    def submit(self):
        """

        :return:
        """
        if len(self) <= 0:
            raise Exception("no source data config to add!")
        for itemSourceData in self:
            bRet = True
            strParams = itemSourceData.getParams(self.strBusId, self.strInterfaceName)
            # strUrl = "{url}?{params}".format(TdbankDataSourceMgr.URL, strParams)

            objNetConn = NetConn(TdbankDataSourceMgr.URL, strParams)
            objResult = objNetConn.request()

            if objResult is None:
                self.strError = objNetConn.getLastError()
                bRet = False
            elif objResult["state"] != "0":
                self.strError = objResult["returnStr"]
                bRet = False
            if bRet is False:
                raise Exception("Add data source config [%s/%s] error:%s" % (
                    self.strInterfaceName, itemSourceData.getIp(), self.strError))


class Field(dict):
    """
    接口管理中所需的字段
    """

    def __init__(self, strName, strType, strComment=""):
        """

        :param strName:
        :param strType:
        :param strComment:
        """
        dict.__init__(self, name=strName, type=strType, comment=strComment)


class TdbankInterfaceMgr(dict):
    """TDBANK接口管理"""
    OPID = 2
    URL = "http://%s:%s/operator" % (IP, PORT)

    def __init__(self, strBusId, strInterfaceName):
        """
        初始化
        :param strBusId:
        :param strInterfaceName:
        """
        self.strBusId = strBusId
        self.strInterfaceName = strInterfaceName
        self.lstFieldList = []
        self.strError = ""
        dict.__init__(self, opid=TdbankInterfaceMgr.OPID, interfaceid=strInterfaceName, businessid=strBusId,
                      interfacename=strInterfaceName, interfacedesc=strInterfaceName, operator=OPERATOR)

    def addConfig(self, objField):
        """

        :return:
        """
        self.lstFieldList.append(objField)

    def submit(self):
        """

        :return:
        """
        if len(self.lstFieldList) <= 0:
            raise Exception("no field in interface config!")
        bRet = True
        objNetConn = NetConn(TdbankInterfaceMgr.URL, self.getParams())
        objResult = objNetConn.request()

        if objResult is None:
            self.strError = objNetConn.getLastError()
            bRet = False
        elif objResult["state"] != "0":
            self.strError = "remote server error, " + objResult["returnStr"]
            bRet = False
        if bRet is False:
            raise Exception("add tdbank interface config [%s] error:%s" % (self.strInterfaceName, self.strError))

    def getParams(self):
        """

        :return:
        """
        self["context"] = ";".join(["{name},{type},{comment}".format(name=itemField["name"],
                                                                                          type=itemField["type"],
                                                                                          comment=itemField["comment"]) for itemField in self.lstFieldList])
        self["fieldArray"] = json.dumps(self.lstFieldList)
        return "&".join(["{key}={value}".format(key=itemKey, value=self[itemKey]) for itemKey in list(self.keys())])


class TdbankTargetMgr(dict):
    """
    tdbank流向配置
    """
    OPID = 3
    URL = "http://%s:%s/operator" % (IP, PORT)
    TDW_POOL = "g_teg_sec_unifiedstorage_g_teg_sec_unifiedstorage_data"
    TDW_SERVER = "tdw_tl"

    def __init__(self, strBusId, strInterfaceName, strPartitionType='day'):
        """

        :param strBusName:
        :param strInterfaceName:
        """
        self.strInterfaceName = strInterfaceName
        self.lstTargetTables = []
        dict.__init__(self, opid=TdbankTargetMgr.OPID, interfacename=strInterfaceName, businessid=strBusId,
                      partitiontype=strPartitionType, operator=OPERATOR, tdw_appgroup=TdbankTargetMgr.TDW_POOL,
                      targeTdwServer=TdbankTargetMgr.TDW_SERVER,
                      tdw_storage_period=-1, tdw_file_format="orcfile",
                      lz_alert_receiver=OPERATOR)

    def addConfig(self, strDbName, strTbName):
        """

        :param strDbName:
        :param strTbName:
        :return:
        """
        self.lstTargetTables.append((strDbName, strTbName))

    def submit(self):
        """

        :return:
        """
        if len(self.lstTargetTables) <= 0:
            raise Exception("no flow target config to submit!")
        for itemTbInfo in self.lstTargetTables:
            """支持同一个接口数据入库到多个表"""
            # strUrl = "{url}?{params}".format(url = TdbankInterfaceMgr.URL, params = self.getParams(*itemTbInfo))
            bRet = True
            objNetConn = NetConn(TdbankInterfaceMgr.URL, self.getParams(*itemTbInfo))
            objResult = objNetConn.request()

            if objResult is None:
                self.strError = objNetConn.getLastError()
                bRet = False
            if objResult["state"] != "0":
                self.strError = objResult["returnStr"]
                bRet = False
            if bRet is False:
                raise Exception("add tdbank flow target config [%s] error:%s" % (self.strInterfaceName, self.strError))

    def getParams(self, strDbName, strTbName):
        """

        :param strDbName:
        :param strTbName:
        :return:
        """
        self["targetdatabase"] = strDbName
        self["targettable"] = strTbName
        return "&".join(["{key}={value}".format(key=itemKey, value=self[itemKey]) for itemKey in list(self.keys())])


class TdbankConfigCenter(object):
    """tdbank配置中心"""

    def __init__(self, strBusId, strInterfaceName):
        """

        :param strBusId:
        :param strInterfaceName:
        """
        self.strError = ""
        self.objTdbankInterfaceMgr = TdbankInterfaceMgr(strBusId, strInterfaceName)
        self.objTdbankSourceMgr = TdbankDataSourceMgr(strBusId, strInterfaceName)
        self.objTdbankFlowTargetMgr = TdbankTargetMgr(strBusId, strInterfaceName)

    def addInterfaceField(self, objField):
        """

        :param objField:
        :return:
        """
        self.objTdbankInterfaceMgr.addConfig(objField)

    def addSourceData(self, objSourceData):
        """

        :param objSourceData:
        :return:
        """
        self.objTdbankSourceMgr.addConfig(objSourceData)

    def addFlowTarget(self, strDbName, strTbName):
        """

        :param strDbName:
        :param strTbName:
        :return:
        """
        self.objTdbankFlowTargetMgr.addConfig(strDbName, strTbName)

    def submit(self):
        """
        提交
        :return:
        """
        try:
            self.objTdbankInterfaceMgr.submit()
            # self.objTdbankSourceMgr.submit()
            self.objTdbankFlowTargetMgr.submit()
            return True
        except Exception as ex:
            self.strError = traceback.format_exc()
            return False

    def getLastError(self):
        """

        :return:
        """
        return self.strError


if __name__ == "__main__":
    objTdbankConfigCenter = TdbankConfigCenter(BUS_ID, "jeffwan2")
    objTdbankConfigCenter.addInterfaceField(Field("test1", "bigint", "test field"))
    objTdbankConfigCenter.addInterfaceField(Field("test2", "string", "test field2"))
    objTdbankConfigCenter.addInterfaceField(Field("test3", "double", "test field3"))
    objTdbankConfigCenter.addSourceData(
        SourceData("10.49.100.10", "/data1/xcube/jeffwan2/mf_tb_files_update_test_YYYYMMDDhh.*txt"))
    objTdbankConfigCenter.addSourceData(
        SourceData("10.49.100.13", "/data1/xcube/jeffwan2/mf_tb_files_update_test_YYYYMMDDhh.*txt"))
    objTdbankConfigCenter.addFlowTarget(strDbName="sec_onion_interface", strTbName="jeffwan2")
    if objTdbankConfigCenter.submit() is False:
        print(objTdbankConfigCenter.getLastError())
