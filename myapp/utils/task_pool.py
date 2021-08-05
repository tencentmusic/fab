#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
File：   task_pool
Description： 任务执行池
Date：   2017/5/22 20:26
Author： Jeffwan
Copyright 1998 - 2017 TENCENT Inc. All Rights Reserved
modify：
    Jeffwan        2017/5/22       Create
"""



import time
import uuid
import copy
import json
import traceback
import queue as threadQueue
from threading import RLock, Thread
from multiprocessing import  Process, Manager
from .log import Log
from datetime import datetime, date


class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")
        else:
            return json.JSONEncoder.default(self, obj)

def JsonDumps(objData):
    return json.dumps(objData, cls = DateEncoder)


class TaskBase(object):
    """任务基类"""

    def __init__(self, dictParams, iPriority, strAppName, strTaskId, iTimeout, iReTryNum, iRetryInterval):
        """
        初始化
        :param dictParams: 参数字段， 会传给onStart
        :param iPriority: 任务优先级
        :param strAppName: 应用名称
        :param strTaskId: 任务ID， 不填的话默认生成一个
        :param iTimeout:任务执行超时时间
        :param iReTryNum:超时重试次数
        :param iRetryInterval:超时重试时的间隔时间
        """
        self.dictParams     = copy.deepcopy(dictParams)
        self.iPriroty       = iPriority
        self.strAppName     = strAppName
        self.iReTryNum      = iReTryNum
        self.iTimeout       = iTimeout
        self.iRetryInterval = iRetryInterval
        self.objStatusMgr   = None
        self.iRunNum        = 0 #已执行次数
        self.strTaskId      = strTaskId if strTaskId is not None else "TaskPool.{app_name}@{uuid}".format(app_name = strAppName, uuid = uuid.uuid1())


    def run(self):
        """
        线程或进程入口
        :return:
        """
        try:
            self.iRunNum += 1
            self.objStatusMgr.setStatus(self.strTaskId, StatusManager.FLAG_RUNNING)
            objResult = self.onStart(self.dictParams)

            #如果执行成功，则返回
            if objResult.iRetCode == 0:
                self.objStatusMgr.setStatus(self.strTaskId, StatusManager.FLAG_SUCC, objResult)
                self.onSucc()
                return
            #执行失败时执行
            self.onFail()
            #执行失败， 要准备重试
            if self.iRunNum < self.iReTryNum + 1:
                self.restart()
            #执行完成的时候执行
            self.onFinish()

            #经过重试还是执行失败，返回结果
            self.objStatusMgr.setStatus(self.strTaskId, StatusManager.FLAG_FAIL, objResult)

        except Exception as ex:
            strMsg = traceback.format_exc()
            Log.wException(strMsg)
            self.objStatusMgr.setStatus(self.strTaskId, StatusManager.FLAG_FAIL, Result(iRetCode=-1, strMsg=str(strMsg)))


    def restart(self):
        """
        重跑
        :return:
        """
        self.run()


    def onStart(self, dictParams):
        """
        起始入口，需重载后调用
        :return:
        """
        raise Exception("Function onStart must be override in child class.")


    def onFail(self):
        """
        失败后调用，需重载
        :return:
        """


    def onSucc(self):
        """
        成功后调用，需重载
        :return:
        """

    def onFinish(self):
        """
        完成后调用，需重载
        :return:
        """


    def onTimeout(self):
        """
        任务超时时调用
        :return:
        """

    def setStatusMgr(self, objStatusManager):
        self.objStatusMgr = objStatusManager



class Result(object):
    """返回结果类"""
    def __init__(self, iRetCode = 0, strMsg = "success", objData = None):
        self.iRetCode     = int(iRetCode)
        self.strMsg       = strMsg
        self.objData      = objData
        assert isinstance(self, Result) is True

    def __repr__(self):
        return '<Result ' + hex(id(self)) + '>'

    def getJsonRet(self):
        try:
            return JsonDumps({"ret_code":self.iRetCode, "msg": self.strMsg, "data": self.objData})
        except Exception as ex:
            return json.dumps({"ret_code":-1, "msg": "dumps result to json error:%s" % traceback.format_exc(), "data": None})

    def getDictRet(self):
        return {"ret_code":self.iRetCode, "msg": self.strMsg, "data": self.objData}



class TaskPool(object):
    """任务池"""

    def __init__(self, iMaxTask = 10):
        """
        初始化
        :param iMaxTask:同时执行的最大任务数
        """
        self.iMaxTask           = iMaxTask
        self.objLock            = RLock()
        self.objTaskQeue        = threadQueue.Queue()
        self.objStatusManager   = StatusManager()
        TaskSchedule(self.objTaskQeue, self.objLock, self.objStatusManager, iMaxTask).start()


    def put(self, objTask):
        """
        添加任务
        :param objTask:
        :return:
        """
        objTask.setStatusMgr(self.objStatusManager)
        strTaskId = objTask.strTaskId
        if self.objStatusManager.hasKey(strTaskId):
            raise Exception("Task id exists:%s" % strTaskId)
        #初始化状态信息
        self.objStatusManager.setStatus(strTaskId, StatusManager.FLAG_READY, objContext = {
            "start_time"    :   time.time(),
            "timeout"       :   objTask.iTimeout
        })

        self.objTaskQeue.put(objTask)

        return strTaskId



    def checkFull(self):
        """
        检查队列是否已经满了
        :return:
        """
        if self.objStatusManager.getStatusTaskNum([StatusManager.FLAG_RUNNING]) >= self.iMaxTask:
            return True
        return False


    def get(self, strTaskId = None, bBlock = True, iTimeout = 30):
        """
        获取结果
        :param strTaskId:
        :param bBlock:
        :param iTimeout:
        :return:
        """
        if strTaskId is not None:
            return self.objStatusManager.getResult(strTaskId, bBlock, iTimeout)

        lstAllTaskId = self.objStatusManager.getKeys()

        lstResult = []

        iStartTime = time.time()

        while 1:
            lstUnFinishedTask = []
            if time.time() - iStartTime > 3600 * 24:
                raise Exception("sql executed timeout!")

            if len(lstAllTaskId) == 0:
                break

            for itemTask in lstAllTaskId:
                objResult = self.objStatusManager.getResult(itemTask, bBlock = False)
                if objResult is None:
                    lstUnFinishedTask.append(itemTask)
                    continue

                #已经取到结果，清理队列中的数据
                self.objLock.acquire()
                self.objStatusManager.delTask(itemTask)
                self.objLock.release()
                lstResult.append(objResult)

            if len(lstUnFinishedTask) == 0:
                break
            lstAllTaskId = lstUnFinishedTask

        return lstResult






class TaskSchedule(Thread):
    """任务调度器"""

    def __init__(self, objTaskQueue, objLock, objStatusMgr, iMaxTask):
        Thread.__init__(self)
        self.setDaemon(True)
        self.objTaskQueue = objTaskQueue
        self.objLock      = objLock
        self.objStatusMgr = objStatusMgr
        self.iMaxTask     = iMaxTask


    def run(self):
        """
        入口
        :return:
        """
        while 1:
            #看同时执行的任务数是否超过上限， 如果超过，则排队等待
            self.objLock.acquire()
            iRunTaskNum = self.objStatusMgr.getStatusTaskNum([StatusManager.FLAG_RUNNING, StatusManager.FLAG_PAUSE])
            self.objLock.release()
            if iRunTaskNum >= self.iMaxTask:
                continue
            objTask = self.objTaskQueue.get(block = True)
            objTask.start()
            #self._clear()


    def _clear(self):
        """
        清理超时任务等
        :return:
        """
        #找出超时任务
        self.objLock.acquire()
        lstTimeOutTasks = [strTaskId for strTaskId in self.objStatusMgr.getKeys() if self.objStatusMgr.checkTimeout(strTaskId)]
        for itemTask in lstTimeOutTasks:
            print(itemTask, "   timeout")
            self.objStatusMgr.delTask(itemTask)
        self.objLock.release()




class StatusManager(object):
    """
    状态管理器
    """
    #校验可以开始执行的任务为READY状态
    FLAG_READY      = 'ready'
    #执行中状态
    FLAG_RUNNING    = 'running'
    #待终止状态
    FLAG_PAUSE      = 'pause'
    #成功状态
    FLAG_SUCC       = 'succ'
    #失败状态
    FLAG_FAIL       = 'fail'


    def __init__(self):
        objManager   = Manager()
        self.objContainer = objManager.dict()


    def set(self, key, value):
        """
        设置值
        :param key:
        :param value:
        :return:
        """
        self.objContainer[key]    =   value


    def get(self, key):
        """
        获取值
        :return:
        """
        if key not in self.objContainer:
            raise Exception("Key not exist in context:%s" % key)
        return self.objContainer[key]


    def hasKey(self, strKey):
        """
        检查字典是否有否个key值
        :param strKey:
        :return:
        """
        return strKey in self.objContainer


    def setStatus(self, strTaskId, strStatus, objResult = None, objContext = None):
        """
        设置某个任务的状态
        :param strTaskId:
        :param strStatus:
        :return:
        """
        if self.hasKey(strTaskId) is False:
            self.objContainer[strTaskId] = {
                "status"    :   strStatus,
                "result"    :   objResult,
                "context"   :   objContext
            }
        else:
            if objResult is not None:
                self.objContainer[strTaskId] = {
                "status"    :   strStatus,
                "result"    :   objResult,
                "context"   :   objContext
                }
            else:
                self.objContainer[strTaskId] = {
                    "status"    : strStatus,
                    "result"    : self.objContainer[strTaskId]["result"],
                    "context"   : self.objContainer[strTaskId]["context"]
                }


    def getTaskTimeout(self, strTaskId):
        """
        获取任务的超时时间
        :param strTaskId:
        :return:
        """
        if self.hasKey(strTaskId) is False:
            return 30

        return self.objContainer[strTaskId]["context"]["timeout"]



    def getTaskStartTime(self, strTaskId):
        """
        获取任务的开始时间
        :param strTaskId:
        :return:
        """
        if self.hasKey(strTaskId) is False:
            return 0

        return self.objContainer[strTaskId]["context"]["start_time"]



    def checkTimeout(self, strTaskId):
        """
        检查任务是否超时
        :return:
        """
        if self.hasKey(strTaskId) is False:
            return False

        return time.time() - self.getTaskStartTime(strTaskId) > self.getTaskTimeout(strTaskId)



    def getKeys(self):
        """
        返回key列表
        :return:
        """
        return list(self.objContainer.keys())


    def getStatus(self, strTaskId):
        """
        获取任务状态
        :param strTaskId:
        :return:
        """
        if self.hasKey(strTaskId) is False:
            raise Exception("Task not exist:%s" % strTaskId)
        return self.get(strTaskId)["status"]


    def getResult(self, strTaskId, bBlock = True, iTimeOut = 30):
        """
        获取任务结果
        :param strTaskId:
        :return:
        """
        if self.hasKey(strTaskId) is False:
            raise Exception("Task not exist:%s" % strTaskId)

        objResult = self.get(strTaskId)["result"]

        iBlockStart = time.time()

        if objResult is not None:
            return objResult
        while 1:
            if not bBlock:
                break

            objResult = self.get(strTaskId)["result"]
            if objResult is not None:
                break

            if time.time() - iBlockStart > iTimeOut:
                break

        return objResult


    def getStatusTaskNum(self, lstStatus):
        """
        获取当前处于某个状态的的任务数
        :param lstStatus: 需要过滤的状态列表
        :return:
        """
        return len([x for x in self.getKeys() if self.get(x)["status"] in lstStatus])



    def delTask(self, strTaskId):
        """
        删除一个任务
        :param strTaskId:
        :return:
        """
        del self.objContainer[strTaskId]



class ThreadTask(TaskBase, Thread):
    """采用线程模式执行的任务"""

    def __init__(self, dictParams = {}, iPriority = 10, strAppName = 'task', strTaskId = None, iTimeout = 30, iReTryNum = 0, iRetryInterval = 30):
        """
        初始化
        :param dictParams: 参数字段， 会传给onStart
        :param iPriority: 任务优先级
        :param strAppName: 应用名称
        :param strTaskId: 任务ID， 不填的话默认生成一个
        :param iTimeout:任务执行超时时间
        :param iReTryNum:超时重试次数
        :param iRetryInterval:超时重试时的间隔时间
        """
        Thread.__init__(self)
        TaskBase.__init__(self, dictParams, iPriority, strAppName, strTaskId, iTimeout, iReTryNum, iRetryInterval)
        #self.setDaemon(True)


    def onStart(self, dictParams):
        """
        入口
        :param dictParams:
        :return:
        """
        raise Exception("OnStart function must be overide")



    def checkAlive(self):
        """
        检查是否存活
        :return:
        """
        return self.isAlive()


    def terminal(self):
        """
        终止线程,python现在不支持
        :return:
        """
        pass


class ProcessTask(TaskBase, Process):
    """采用进程模式执行的任务"""

    def __init__(self, dictParams = {}, iPriority = 10, strAppName = 'task', strTaskId = None, iTimeout = 30, iReTryNum = 0, iRetryInterval = 30):
        """
        初始化
        :param dictParams: 参数字段， 会传给onStart
        :param iPriority: 任务优先级
        :param strAppName: 应用名称
        :param strTaskId: 任务ID， 不填的话默认生成一个
        :param iTimeout:任务执行超时时间
        :param iReTryNum:超时重试次数
        :param iRetryInterval:超时重试时的间隔时间
        """
        TaskBase.__init__(self, dictParams, iPriority, strAppName, strTaskId, iTimeout, iReTryNum, iRetryInterval)
        Process.__init__(self)
        #self.daemon = True


    def onStart(self, dictParams):
        """
        入口
        :param dictParams:
        :return:
        """
        raise Exception("OnStart function must be overide")


    def checkAlive(self):
        """
        检查是否存活
        :return:
        """
        return self.is_alive()


class TestTask(ThreadTask):
    """数据操作基类"""


    def __init__(self):
        """
        初始化
        :param strSchType: 调度类型
        :param strSchValue: 调度值， 如果是定时触发， 格式与contab一致， 否则填依赖任务ID
        """
        ThreadTask.__init__(self)



    def onStart(self, dictParams):
        """
        自动触发
        :param dictParams:
        :return:
        """
        return Result()


if __name__ == '__main__':

    objTaskPool = TaskPool(iMaxTask = 100)

    objTask = TestTask()
    objTaskPool.put(objTask)
    lstResult = objTaskPool.get()
    print("Result:", lstResult)
