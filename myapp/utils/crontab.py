# -*- coding:utf-8 -*-
"""
des: 
create time: 2015-7-28 
version: 
author: jeffwan
function:  
Copyright 1998 - 2017 TENCENT Inc. All Rights Reserved
modify:
    <JEFFWAN>        <modify time>       <des>
"""

import time

class _Crontab(object):
    """定时任务管理"""

    def __call__(self, strCronValue, iUnixTime = None):
        """
        检查是否应该触发
        :param strCronValue:
        :return:
        """
        lstItem = strCronValue.strip().split(" ")
        if len(lstItem) != 5 :
            raise Exception("Crontab format error:eg.  */30 2-9 * * *")

        lstResult  = []
        i = 0
        for item in lstItem:
            if self._itemCheck(i, item, iUnixTime):
                lstResult.append(item)
            i += 1
        if len(lstResult) != 5:
            return False
        return True


    def _itemCheck(self, iIndex, strCronValue, iUnixTime):
        """
        格式检查
        :param strCronValue:
        :return:

        """
        current = int(self._getCurent(iIndex, iUnixTime))
        if strCronValue == "*":
            return True
        iFindDot   = strCronValue.find("*")
        iFindLine  = strCronValue.find("-")
        find_lead  = strCronValue.find("/")

        if iFindDot == -1 and iFindLine == -1 and find_lead == -1 and int(strCronValue) == current:
            return True

        if iFindLine != -1 and find_lead == -1:
            timestart, timeend = [int(x.strip()) for x in strCronValue.split("-")]
            if timestart <= current and timeend >= current:
                return True
            return False
        elif find_lead != -1 and iFindLine == -1:
            timestart, interval = [int(x.strip()) if x != "*" else "*" for x in strCronValue.split("/")]
            if current % interval == 0:
                return True
            return False
        elif find_lead != -1 and iFindLine != -1:
            timestart, timeend, interval = [int(x.strip()) if x != "*" else "*" for x in strCronValue.replace("-", "/").split("/")]
            if current < timestart or current > timeend:
                return False
            if current % interval == 0:
                return True
            return False
        return False


    def _getCurent(self, iIndex, iUnixTime):
        """
        获取当前值
        :param iIndex:
        :return:
        """
        if iIndex == 0:
            return self.getDatetime("%M", iUnixtime = iUnixTime)
        if iIndex == 1:
            return self.getDatetime("%H", iUnixtime = iUnixTime)
        if iIndex == 2:
            return self.getDatetime("%d", iUnixtime = iUnixTime)
        if iIndex == 3:
            return self.getDatetime("%m", iUnixtime = iUnixTime)
        if iIndex == 4:
            return self.getDatetime("%w", iUnixtime = iUnixTime)


    def getDatetime(self, strFormart="%Y-%m-%d %H:%M:%S", iUnixtime=None):
        """
        获取当前时间
        :param strFormart:时间格式化
        :param iUnixtime:
        :return:"%Y-%m-%d %H:%M:%S"形式的字符串
        """
        iUnixtime = time.time() if iUnixtime is None else iUnixtime
        return time.strftime(strFormart, time.localtime(iUnixtime))


Crontab = _Crontab()


if __name__ == "__main__":
    print(Crontab("* * * * *"))