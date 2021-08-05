# -*- coding:utf-8 -*-
"""
des: tdw元数据服务客户端, 这里只是接口定义，不是接口实现
create time: 
version: 
"""

from typing import Any, Callable, Dict, List, Optional, Tuple, Union, overload

class TdwMetaData:
    """tdw元数据服务客户端"""

    def __init__(self, username:str, cmk:str, service:str, meta_server:str = None, auth_server:str = None):
        """
        初始化客户端
        :param username: 请求元数据接口的用户名
        :param cmk: tdw鉴权系统中的cmk
        :param service: 请求的服务名称
        :param meta_server:手动指定元数据server地址
        :param auth_server:手动指定auth_server地址
        """


    def get_table_instore_us_task(self, db: str = None, table: str = None):
        """
        根据库名和表名获取对应的入库洛子任务
        :param db:数据库名
        :param table:表名
        :return:
        """


    def get_bg_budget(self, bgName: str = None, planProduct: str = None):
        """
        查询某个BG或产品的预算
        :param bgName:BG全称，例如：IEG互动娱乐事业群
        :param planProduct:规划产品，例如：微信支付，可省略
        :return: 
        """


    def list_us_tasks(self, bgId: str = None, productName: str = None):
        """
        获取BG或者产品下的全部洛子任务
        :param bgId:事业群id，例如WXG
        :param productName:规划产品名称，例如：微信支付
        :return: 
        """


    def get_us_task_link(self, taskId: str = None, direction: str = None):
        """
        获取洛子任务的上下游
        :param taskId:洛子任务id
        :param direction:input表示查任务的上游，output表示查任务的下游，both表示查任务的上下游
        :return: 
        """


    def get_table_query_frequency(self, cluster: str = None, db: int = None, table: str = None):
        """
        查询表的访问频率
        :param cluster:集群，例如tl
        :param db:库名
        :param table:表名
        :return: 
        """


    def get_bus_table_with_sensitivity(self, productName: str = None):
        """
        查看某业务下所有表的敏感等级
        :param productName:规划产品名称,仅限产品owner体验
        :return: 
        """


    def get_hive_table_query_record(self, cluster: str = None, db: int = None, table: str = None, startTime: int = None, endTime: int = None):
        """
        hive访问记录：按库表查询
        :param cluster:集群，例如tl
        :param db:库名
        :param table:表名
        :param startTime:开始时间unix
        :param endTime:结束时间unixtime
        :return: 
        """


    def get_us_task_view(self, viewId: str = None):
        """
        获取视图（画布）下的所有作业依赖关系
        :param viewId:画布id
        :return: 
        """


    def get_us_task_detail(self, id: str = None):
        """
        获取洛子任务的详情信息
        :param id:洛子任务id
        :return: 
        """


    def get_table_partitions(self, dbName: str = None, tbName: str = None, isPrimary: str = None, limit: int = None, offset: int = None):
        """
        查询表的分区列表
        :param dbName:库名
        :param tbName:表名
        :param isPrimary:是否查询主分区
        :param limit:返回结果条数
        :param offset:页码偏移
        :return: 
        """


    def list_bg_groups(self, bgId: str = None, pdName: str = None):
        """
        查询BG或产品下的全部应用组列表
        :param bgId:BG名称，例如WXG
        :param pdName:规划产品名称，例如：微信支付
        :return: 
        """


    def show_tables(self, dbName: str = None):
        """
        查询库下的全部表
        :param dbName:库名
        :return: 
        """


    def set_table_reserve_days(self, cluster: str = None, dbName: str = None, tableName: str = None, reservedday: int = None, keepLastDayPerMonth: int = None, userName: str = None):
        """
        设置表的生命周期(保存天数)
        :param cluster:集群，默认tl
        :param dbName:库名
        :param tableName:tableName
        :param reservedday:保存天数
        :param keepLastDayPerMonth:保存策略，默认为1，非必填参数
        :param userName:请求求改的用户名，例如jeffwan
        :return: 
        """


    def get_user_tables(self, tdwUser: str = None, size: str = None, offset: str = None):
        """
        查询用户有权限的库表
        :param tdwUser:tdw用户名
        :param size:返回的每页数据条数
        :param offset:页码偏移
        :return: 
        """


    def confirm_user_select_priv(self, cluster: str = None, database: str = None, tableName: str = None, tdwUser: str = None):
        """
        查询某个用户是否有权限读取某张表
        :param cluster:集群名称，例如：tl
        :param database:数据库名称
        :param tableName:表名
        :param tdwUser:tdw用户名，例如:tdw_jeffwan
        :return: 
        """


    def get_bg_storage_cost(self, bgName: str = None, planProduct: str = None):
        """
        查询某个BG或产品的存储成本
        :param bgName:BG全程，例如：IEG互动娱乐事业群
        :param planProduct:规划产品，例如：微信支付，可省略
        :return: 
        """


    def get_us_instance_state(self, taskId: str = None, startDate: str = None, endDate: str = None):
        """
        获取洛子任务运行状态
        :param taskId:洛子任务id
        :param startDate:任务运行的数据日期的起始，例如：1561928400000
        :param endDate:任务运行的数据日期的结束，例如：1571932000000
        :return: 
        """


    def list_users(self, appgroup: str = None):
        """
        列出应用组下全部用户列表
        :param appgroup:None
        :return: 
        """


    def get_hive_user_query_record(self, cluster: str = None, db: int = None, table: str = None, startTime: int = None, endTime: int = None, userName: str = None):
        """
        hive访问记录：按用户查询
        :param cluster:集群，例如tl
        :param db:库名
        :param table:表名
        :param startTime:开始时间unix
        :param endTime:结束时间unixtime
        :param userName:企业微信用户名
        :return: 
        """


    def query_tb_idex_export_record(self, cluster: str = None, db: int = None, table: str = None, startTime: int = None, endTime: int = None, size: int = None, offset: int = None):
        """
        IDEX导出记录：按库表查询
        :param cluster:集群，例如tl
        :param db:库名
        :param table:表名
        :param startTime:开始时间unix
        :param endTime:结束时间unixtime
        :param size:导出数据条数
        :param offset:页码偏移
        :return: 
        """


    def get_calculate_cost(self, bgName: str = None, planProduct: str = None):
        """
        查询某个BG/规划产品的计算成本
        :param bgName:BG全称，例如:CSIG云与智慧产业事业群
        :param planProduct:规划产品：例如微信支付
        :return: 
        """


    def show_databases(self, appgroup: str = None):
        """
        列表应用组下的全部库
        :param appgroup:用用组id, 例如：g_wxg_wechat_pay
        :return: 
        """


    def set_tb_sensitivity(self, tableSensitivities: list = None, group: str = None, db: str = None, cluster: str = None):
        """
        设置表的敏感等级
        :param tableSensitivities:None
        -->:sub-param comment:备注信息
        -->:sub-param sensitivity:要设置的敏感等级：0普通，1敏感，2高敏感
        -->:sub-param dbName:库名，可省略，因为外层参数已有
        -->:sub-param tableName:要设置的表名
        :param group:此次登陆用户的应用组，目前可选
        :param db:库名
        :param cluster:库表在的集群
        :return: 
        """


    def query_tb_lifetime_modify_state(self, approveId: str = None):
        """
        查看生命周期设置的审批状态
        :param approveId:审批单id，由set_table_reserve_days接口返回
        :return: 
        """


    def get_table_detail(self, dbName: str = None, tbName: str = None):
        """
        查询表的元数据信息
        :param dbName:库名
        :param tbName:表名
        :return: 
        """


    def get_us_task_belong_view_list(self, taskId: str = None):
        """
        获取洛子任务所属的视图（画布）列表
        :param taskId:洛子任务id
        :return: 
        """


    def get_user_groups(self, tdwUser: str = None):
        """
        查询用户有权限的应用组：用户所属的应用组
        :param tdwUser:tdw用户名
        :return: 
        """


    def query_user_idex_export_record(self, startTime: int = None, endTime: int = None, user: str = None):
        """
        IDEX导出记录：按用户查询
        :param startTime:开始时间unix
        :param endTime:结束时间unixtime
        :param user:用户企业微信用户名
        :return: 
        """