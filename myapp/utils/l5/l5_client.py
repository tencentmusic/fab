# -*- coding:utf-8 -*-
"""
des: 
create time: 
version: 
"""
from . import l5sys


def get_route(mod_id, cmd_id):
    """
    根据modId cmdId获取l5的路由
    
    :param mod_id: 
    :param cmd_id:
    :return: 
    """
    ret, qos = l5sys.ApiGetRoute({'modId': mod_id, 'cmdId': cmd_id}, 0.2)
    if ret != 0:
        return None
    return qos['hostIp'], repr(qos['hostPort'])
