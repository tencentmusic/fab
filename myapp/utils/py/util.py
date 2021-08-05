# -*- coding: utf-8 -*-
# 公共函数
import json,time,datetime

#响应状态
STATUS_CODE = {
    'success': 0,
    'unknow_error': 1,
}

# 构造响应数据
def write_response(success=STATUS_CODE['success'], msg='success'):
    if success != STATUS_CODE['success']:
        return json.dumps({'message': msg}), 400
    else:
        return json.dumps({'message': msg}), 200








