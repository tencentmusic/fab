# -*- coding:utf-8 -*-
"""
des: 
create time: 
version: 
"""

import re
import uuid
import threading
import sqlparse
from src.utils.config import Config
from src.utils.date_time import datadesc
from src.utils.hive_jdbc.hive_jdbc import HiveJdbc
from src.utils.date_time import *
from src.utils.log import Log
from src.framework.consts import *
from src.utils.utils import md5
from threading import Lock
from src.utils.utils import to_string


class _HiveConnectition(object):
    """
    单个hiveL连接
    """

    RETIRE = 3600

    def __init__(self, jdbc_key, conn):
        """

        :param jdbc_key:
        :param conn:
        """
        self.jdbc_key = jdbc_key
        self.conn = conn
        self.create_time = unix_timestamp()


    def check_retire(self):
        """

        :return:
        """
        if unix_timestamp() - self.create_time > _HiveConnectition.RETIRE:
            return True
        return False


    def free(self):
        """

        :return:
        """
        HiveConnectionPool.set_free(self.jdbc_key, self.conn)


    def close(self):
        """

        :return:
        """
        self.conn.close()


class _HiveConnectionPool(object):
    """
    hive连接池
    """

    def __init__(self):
        """
        初始化
        """
        self.jdbc_map = {}
        self.__lock = Lock()


    def get_connection(self, host, port, db, user, passwd):
        """

        :param host:
        :param port:
        :param db:
        :param user:
        :param passwd:
        :return:
        """
        try:
            self.__lock.acquire()
            jdbc_key = self.__key(host, port, db, user, passwd)
            #初始化jdbc
            if (jdbc_key in self.jdbc_map) is False:
                jdbc_url = 'jdbc:hive://%s:%s/%s' % (host, port, db)
                class_path = ["%s/src/utils/hive_jdbc/jar/JDBCBridge.jar" % Config.ROOT,
                              "%s/src/utils/hive_jdbc/jar/hive_jdbc.jar" % Config.ROOT]
                self.jdbc_map[jdbc_key] = {}
                self.jdbc_map[jdbc_key]["jdbc"] = HiveJdbc(HiveClient.DRIVER_NAME, jdbc_url, user, passwd, class_path)
                self.jdbc_map[jdbc_key]["connections"] = []
            connection = None
            while 1:
                connection = self.__create_or_reuse_conn(jdbc_key)
                if connection.check_retire():
                    try:
                        connection.close()
                    except Exception as ex:
                        Log.debug("close connection %s failed, %s" % (id(connection), str(ex)))
                else:
                    break
            if connection is None:
                raise Exception("get connection failed, unknown error")
            return connection
        finally:
            self.__lock.release()


    def __create_or_reuse_conn(self, jdbc_key):
        """

        :param jdbc_key:
        :return:
        """
        # 没有可复用的连接
        pool_size = len(self.jdbc_map[jdbc_key]["connections"])
        if pool_size == 0:
            conn = self.jdbc_map[jdbc_key]["jdbc"].connect()
            connection = _HiveConnectition(jdbc_key, conn)
            return connection
        else:
            connection = self.jdbc_map[jdbc_key]["connections"].pop(0)
            Log.debug("reuse jdbc connection %s" % id(connection))
            return connection


    def set_free(self, jdbc_key, connection):
        """

        :param jdbc_key:
        :param connection:
        :return:
        """
        try:
            self.__lock.acquire()
            if jdbc_key not in self.jdbc_map:
                connection.close()
                Log.debug("hive connection closed for jdbc %s" % jdbc_key)
                return
            self.jdbc_map[jdbc_key]["connections"].append(connection)
            Log.debug("set connection %s free for reuse" % id(connection))
        finally:
            self.__lock.release()


    def __key(self, host, port, db, user, passwd):
        """

        :param host:
        :param port:
        :param db:
        :param user:
        :param passwd:
        :return:
        """
        return md5("|".join([str(item) for item in [host, port, db, user, passwd]]))



#hive连接池
HiveConnectionPool = _HiveConnectionPool()


class HiveClient(object):
    """
    hive 客户端
    """
    DRIVER_NAME = "org.apache.hadoop.hive.jdbc.HiveDriver"

    METHODS = []

    def __init__(self, host, port, user, passwd, group_id, db, params = {}):
        """
        注意，非线程安全
        :param host:
        :param port:
        :param user:
        :param passwd:
        :param group_id:资源池id
        :param class_path: jar包路径
        :param service_level:online/offline
        """
        self.host       =   host
        self.port       =   port
        self.user       =   user
        self.passwd     =   passwd
        self.group_id   =   group_id
        self.service_level = "online"
        self.db         =   db
        self.params     =   {} if params is None else params
        self.__connection     =   None
        self.__cursor         =   None
        self.__jdbc_key       =   None


    def __set_default_params(self):
        """
        设置默认的执行参数
        :return:
        """
        self.params["hive.tdwide.sql.rtxuser"] = self.user
        self.params["tdw.ugi.groupname"] = self.group_id
        self.params["mapred.job.tdw.servicelevel"] = self.service_level
        self.params["hive.execute.engine"] = "spark"
        self.params["mapreduce.reduce.speculative"] = "true"
        self.params["mapreduce.task.timeout"] = 12000000
        self.params["select.max.limit"] = 1000000
        self.params["spark.speculation"] = "true"


    def set_pool(self, group_id):
        """
        修改运行sql的资源池
        :param group_id:
        :return:
        """
        self.params["tdw.ugi.groupname"] = group_id


    def set_params(self, key, value):
        """
        设置执行参数
        :param key:
        :param value:
        :return:
        """
        self.params[key] = value


    def set_usp_param(self, job_id = None, data_desc = None):
        """

        :return:
        """
        job_id = job_id if job_id is not None else str(uuid.uuid1())
        data_desc = data_desc if data_desc is not None else datadesc()
        usp_param = "%s_%s" % (job_id, data_desc)
        self.__cursor.execute("set usp.param=%s" % usp_param)
        return usp_param


    def __connect(self):
        """
        连接数据库
        :return:
        """
        if self.__connection is None:
            self.__connection = HiveConnectionPool.get_connection(self.host, self.port, self.db, self.user, self.passwd)
            self.__cursor = self.__connection.conn.cursor()


    def select(self, sql, params = None):
        """

        :param sql:
        :param params:
        :return:
        """
        self.__connect()
        self.__set_params()
        if params is not None:
            sql = sql.format(**params)
        for item_sql in sqlparse.parse(sql):
            self.__cursor.execute(str(item_sql))
        return self.__cursor.fetchall()


    def excute(self, sql, params = None, usp_param = None):
        """

        :param sql:
        :param params:
        :return:
        """
        self.__connect()
        usp_param = self.set_usp_param() if usp_param is None else usp_param
        self.__set_params()
        if params is not None:
            sql = sql.format(**params)
        for item_sql in sqlparse.parse(sql):
            self.__cursor.execute(str(item_sql).rstrip().rstrip(";"))
        if Config.ENV == ENV_DEV:
            Log.debug("[%s]executed sql %s" % (usp_param, sql))


    def __set_params(self):
        """

        :return:
        """
        for key, value in list(self.params.items()):
            command = "set %s=%s;" % (key, value)
            self.__cursor.execute(command)


    def get_partition_field(self, db_name, tb_name):
        """
        获取分区字段
        :param tb_name:
        :return:
        """
        sql = """DESCRIBE EXTENDED {db_name}::{tb_name};""".format(db_name=db_name, tb_name=tb_name)
        p_field = None
        for item_feild in self.select(sql):
            fld_name, fld_type, fld_comment = tuple(item_feild)
            if fld_name != "Detailed Table Information":
                continue
            lst_found = re.findall(r"parKey:FieldSchema\(name:([a-zA_Z0-9]+)", fld_type)
            if len(lst_found) == 1:
                p_field = lst_found[0]
            elif len(list(set(item[0] for item in lst_found))) > 1:
                raise Exception("table can not has more than 1 partition field")
        return p_field


    def check_table_exist(self, db_name, tb_name):
        """

        :param tb_name:
        :return:
        """
        sql = """desc {db_name}::{tb_name};""".format(db_name=db_name, tb_name=tb_name)
        self.excute(sql)
        result = self.__cursor.fetchall()[0][0]
        if result.find("does not exist") != -1:
            return False
        return True


    def partitions(self, db_name, tb_name):
        """
        获取表的全部分区列表，返回集合类型
        :param tb_name:
        :return:
        """
        sql = "use {db_name};show partitions {tb_name}".format(tb_name=tb_name, db_name=db_name)
        self.excute(sql)
        pattern = r"""^p_[0-9]+$"""
        return sorted(list(set(
            [item[0] for item in self.__cursor.fetchall() if re.match(pattern, item[0])])))


    def desc(self, db_name, tb_name):
        """
        获取表结构
        :param db_name:
        :param tb_name:
        :return:
        """
        sql = "desc {db_name}::{tb_name}".format(db_name = db_name, tb_name = tb_name)
        self.excute(sql)
        #注意，这里需要对字段进行一下校验，当tdw表的字段备注信息中存在换行时，tdw会将换行后的备注作为一个单独字段返回
        columns = []
        index = 0
        for item_field in self.__cursor.fetchall():
            field_name, field_type, comment = tuple(item_field)
            if not field_type.strip() or not field_name.strip():
                if index == 0:
                    raise Exception("field type can not be null")
                columns[-1][-1] += "\n%s%s%s" % (field_name, field_type, comment)
                continue
            columns.append([field_name, field_type, comment])
            index += 1
        return columns


    def show_tables(self, database):
        """

        :param database:
        :return:
        """
        sql = "use {db_name};show tables".format(db_name = database)
        self.excute(sql)
        return [item[0] for item in self.__cursor.fetchall()]


    def check_partition_exist(self, db_name, tb_name, partition):
        """

        :param tb_name:
        :param partition:
        :return:
        """
        sql = "select * from {db_name}::{tb_name} PARTITION({partition}) _p1 limit 1".format(
            db_name = db_name,
            tb_name = tb_name,
            partition = partition
        )
        print(sql)
        try:
            self.excute(sql)
        except Exception as ex:
            if str(ex).find("wrong pri-partition name") != -1:
                return False
            raise Exception("check partition exist failed, %s" % str(ex))
        return True


    def add_partition(self, db_name, tb_name, partition):
        """
        添加分区
        :param tb_name:
        :param partition:
        :return:
        """
        if str(partition).isdigit() is False:
            raise Exception("partition must be date, e.g 19700101")
        sql = """use {db_name}; ALTER TABLE {tb_name} ADD PARTITION p_{partition} VALUES IN ({partition})""".format(
            tb_name=tb_name, partition=partition, db_name=db_name)
        self.excute(sql)
        return self.__cursor.fetchall()


    def create_table(self, db_name, tb_name, structure, use_partition = True, store = "orcfile"):
        """

        :param tb_name:
        :param structure:
        :param use_partition:
        :param store:
        :return:
        """
        if structure.p_field is None and use_partition is True:
            raise Exception("no partition field found while create it with param `use_partition` is True ")
        sql = """
            use {db_name};
             CREATE TABLE 
                {tb_name}
            ({fields}) 
            partition by list({p_field})
            (partition default)
            STORED AS {store}    
        """.format(tb_name=tb_name,
                   fields=",".join("%s %s " % (item.name, item.type) for item in structure),
                   p_field=structure.p_field,
                   store=store,
                   db_name=db_name)
        self.excute(sql)



    def drop_table(self, db_name, tb_name):
        """
        删除表，慎用
        :param tb_name:
        :return:
        """
        sql = "use {db_name};drop table {tb_name}".format(db_name=db_name, tb_name=tb_name)
        self.excute(sql)


    def rowcount(self, db_name, tb_name, p_name = None):
        """
        返回表的行数
        :param tb_name:
        :param p_name:
        :return:
        """
        try:
            if p_name is None:
                sql = """use {db_name};show rowcount {tb_name}""".format(
                    db_name=db_name,
                    tb_name=tb_name
                )
            else:
                sql = """use {db_name};show rowcount {tb_name} partition({p_name})""".format(
                    db_name=db_name,
                    tb_name=tb_name,
                    p_name=p_name
                )
            self.excute(sql)
            result = self.__cursor.fetchall()
            if p_name is None:
                return int(result[0][1])
            else:
                return int([item[1] for item in result if item[0] != "pri partitions:"][0])
        except Exception as ex:
            #show rowcount是单机统计，对hive的压力会比较大，可能会失败，则切换到count预计进行统计。
            if str(ex).find("sys error happen to show row count") == -1:
                raise Exception("show rowcount for table %s::%s with partition %s failed, %s" % (db_name, tb_name, p_name, str(ex)))
            if p_name is None:
                sql = """select count(1) from {db_name}::{tb_name}""".format(
                    db_name=db_name,
                    tb_name=tb_name
                )
            else:
                sql = """select count(1) from {db_name}::{tb_name} partition({p_name}) _p1""".format(
                    db_name=db_name,
                    tb_name=tb_name,
                    p_name=p_name
                )
            return self.select(sql)[0][0]


    def truncate(self, db_name, tb_name, p_name = None):
        """
        清空表或分区
        :param tb_name:
        :param p_name:
        :return:
        """
        if p_name is None:
            sql = """use {db_name};truncate table {tb_name}""".format(
                db_name=db_name,
                tb_name=tb_name
            )
        else:
            sql = """use {db_name};ALTER TABLE {tb_name} TRUNCATE PARTITION ({p_name});""".format(
                db_name=db_name,
                tb_name=tb_name,
                p_name=p_name
            )
        self.excute(sql)


    def show_granted_databases(self, role = None):
        """
        列出有权限访问的db
        :return:
        """
        sql = "show grants for {user_name};".format(user_name=self.user if role is None else role)
        result = self.select(sql)
        databases = []
        pattern = r"""grant ([a-z_,\s]+) on ([a-z0-9_]+).([a-z0-9_\*]+)"""
        for item in result:
            item = item[0]
            if item.startswith("GRANT"):
                grants = re.findall(pattern, item.lower(), re.I)
                if len(grants) != 1:
                    continue
                priv, db_name, tb_name = grants[0]
                databases.append(db_name)
        return list(set(databases))


    def show_granted_tables(self, group_id = None):
        """

        :param user_name:
        :return:
        """
        if group_id is not None:
            self.set_pool(group_id)
        sql = "show grants for {user_name};".format(user_name=self.user if group_id is None else group_id)
        result = self.select(sql)
        granted_tables = []
        grants_list = []
        for item in result:
            item = item[0]
            if item.startswith("GRANT"):
                grants_list.append(item)
        # 解析表对应的权限
        list(map(lambda item_grant : self.__parse_grants(item_grant, granted_tables), grants_list))
        return granted_tables


    def show_granted_roles(self):
        """
        查询角色拥有的应用组角色
        :return:
        """
        sql = "show grants for {user_name};".format(user_name=self.user)
        result = self.select(sql)
        granted_roles = None
        for item in result:
            item = item[0]
            if item.startswith("Play roles:"):
                granted_roles = [item.strip() for item in item.replace("Play roles:", "").strip().split(" ")]
                break
        return granted_roles


    def __parse_grants(self, grant_info, granted_tables):
        """
        格式样例GRANT SELECT ON wxg_wechat_pay_app.t_inf_mmpayfetchlimitkv_tkv_fetchlimitmain_fht0
        :param grant_info:
        :return:
        """
        if isinstance(grant_info, str) is False:
            return None
        pattern = r"""grant ([a-z_,\s]+) on ([a-z0-9_]+).([a-z0-9_\*]+)"""
        grants = re.findall(pattern, grant_info.lower(), re.I)
        if len(grants) == 0:
            return None
        elif len(grants) == 1:
            priv, db_name, tb_name = grants[0]
            priv = [item.strip().lower() for item in priv.strip().split(",")]
            if tb_name.strip() == "*":
                #查询库下面的所有表
                self.excute("use {db_name};show tables;".format(db_name = db_name))
                tables = [item_table[0] for item_table in self.__cursor.fetchall()]
                from_database = True
                for item_table in tables:
                    granted_tables.append(
                        (db_name, item_table, priv, from_database)
                    )
            else:
                from_database = False
                granted_tables.append(
                    (
                        db_name,
                        tb_name,
                        priv,
                        from_database
                    )
                )
        else:
            raise Exception("grants info parsed failed, %s" % grant_info)



    def table_detail(self, db_name, tb_name):
        """
        查询表的详情信息
        :param db_name:
        :param tb_name:
        :return:
        """
        sql = """DESCRIBE EXTENDED {db_name}::{tb_name};""".format(db_name=db_name, tb_name=tb_name)
        meta_info = None
        join_string = False
        contents = []
        for item_feild in self.select(sql):
            fld_name, fld_content, fld_comment = tuple(item_feild)
            if fld_name != "Detailed Table Information" and join_string is False:
                continue
            join_string = True
            contents.append("".join([to_string(item) for item in item_feild]))
        if len(contents) > 0:
            meta_info = "\n".join(contents)
        else:
            raise Exception("metadata info from hive does not found")
        return TableMetdaData(self, db_name, tb_name, meta_info)


    def __enter__(self):
        """

        :return:
        """
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        """

        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        self.close()


    def close(self):
        """

        :return:
        """
        if self.__connection is not None and self.__jdbc_key is not None:
            try:
                self.__connection.free()
            except Exception as ex:
                Log.error("close hive connection failed, %s" % str(ex))


class TableMetdaData(dict):

    from collections import OrderedDict

    P_MODE_UNKOWN = "unknow"
    P_MODE_NO_PARTITION = "noncyclic"
    P_MODE_MINIUTE = "minute"
    P_MODE_HOUR = "hour"
    P_MODE_DAY = "day"
    P_MODE_WEEK = "week"
    P_MODE_MONTH = "month"
    P_MODE_YEAR = "year"

    PART_TYPE_DEFINE = OrderedDict({
        P_MODE_YEAR: ("%Y", "years", 4),
        P_MODE_MONTH: ("%Y%m", "months", 6),
        P_MODE_DAY : ("%Y%m%d", "days", 8),
        P_MODE_HOUR : ("%Y%m%d%H", "hours", 10),
        P_MODE_MINIUTE : ("%Y%m%d%H%M", "minutes", 12),
        P_MODE_WEEK: ("%Y%m%d", "weeks", 8)
    })

    def __init__(self, hive, db_name, tb_name, meta_info):
        """

        :param hive:
        :param meta_info:
        """
        part_field = self.__parse_partition_field(meta_info)
        partitions = hive.partitions(db_name, tb_name) if part_field is not None else []
        columns = hive.desc(db_name, tb_name)
        self.hive = hive
        dict.__init__(self,
                      db_name = db_name,
                      tb_name = tb_name,
                      part_field = part_field,
                      owner = self.__parse_owner(meta_info),
                      location = self.__parse_hdfs_path(meta_info),
                      create_time = self.__parse_create_time(meta_info),
                      layer = self.__get_table_layer(tb_name),
                      partitions = partitions,
                      full_table_name = "%s::%s" % (db_name, tb_name),
                      part_count = len(partitions),
                      newest_part = self.__get_newest_part(partitions),
                      oldest_part = self.__get_oldest_part(partitions),
                      columns = columns,
                      part_type = self.get_part_type(tb_name, partitions) if part_field is not None else TableMetdaData.P_MODE_NO_PARTITION
                      )


    def get_newest_part_rowcount(self):
        """
        获取最新分区的行数
        :param partition_name:
        :return:
        """
        return self.hive.rowcount(self.db_name, self.tb_name, self.newest_part)


    def __getattr__(self, item):
        """

        :param item:
        :return:
        """
        return self[item]


    def __get_newest_part(self, partitions):
        """

        :param partitions:
        :return:
        """
        if len(partitions) > 0:
            return partitions[-1]
        return None


    def __get_oldest_part(self, partitions):
        """

        :param partitions:
        :return:
        """
        if len(partitions) > 0:
            return partitions[0]
        return None


    def get_part_type(self, tb_name, partitions):
        """

        :param partitions:
        :return:
        """
        # 解析分区类型
        part_type = TableMetdaData.P_MODE_UNKOWN
        if len(partitions) > 0:
            # 根据日期拍尝试
            test_partition = partitions[0].replace("p_", "")
            for p_type, date_info in list(TableMetdaData.PART_TYPE_DEFINE.items()):
                time_format, _, length = date_info
                if p_type == TableMetdaData.P_MODE_WEEK:
                    continue
                if len(test_partition) != length:
                    continue
                check = self.__check_partition_type(test_partition, time_format)
                if check:
                    part_type = p_type
                    break
        # 根据名称来作为补充
        for p_type, date_info in list(TableMetdaData.PART_TYPE_DEFINE.items()):
            time_format, _, length = date_info
            if len(partitions) > 0:
                test_partition = partitions[0].replace("p_", "")
                if tb_name.endswith("_%s" % p_type) and length == len(test_partition):
                    part_type = p_type
            else:
                if tb_name.endswith("_%s" % p_type):
                    part_type = p_type
        return part_type


    def __check_partition_type(self, p_name, time_format):
        """

        :param p_type:
        :param time_format:
        :return:
        """
        try:
            # 如果不符合，会直接抛出异常
            date2unix(p_name, time_format)
            return True
        except:
            return False


    def __get_table_layer(self, tb_name):
        """

        :param db_name:
        :param tb_name:
        :return:
        """
        layer = "unknown"
        check_rules = [
            ("t_inf", "inf"),
            ("t_dw", "dw"),
            ("t_dm", "dm"),
            ("t_dim", "dim"),
            ("t_tmp", "tmp"),
            ("log_", "inf")
        ]
        for rule, item_layer in check_rules:
            if tb_name.startswith(rule):
                layer = item_layer
                break
        return layer


    def __parse_create_time(self, meta_info):
        """
        解析创建时间
        :param meta_info:
        :return:
        """
        pattern = r"""createTime:([0-9]+),"""
        lst_found = re.findall(pattern, meta_info, re.I)
        if len(lst_found) == 0:
            return None
        return int(lst_found[0])


    def __parse_hdfs_path(self, meta_info):
        """

        :param meta_info:
        :return:
        """
        pattern = r"""location:hdfs://([a-z0-9_\-\.\/]+),"""
        lst_found = re.findall(pattern, meta_info, re.I)
        if len(lst_found) == 0:
            return None
        elif len(lst_found) == 1:
            return "hdfs://%s" % lst_found[0]
        else:
            raise Exception("each table should have 1 hdfs location, found %s" % len(lst_found))


    def __parse_owner(self, meta_info):
        """

        :param raw_info:
        :return:
        """
        pattern = r"owner:([a-z0-9_\-;]+),"
        lst_found = re.findall(pattern, meta_info, re.I)
        if len(lst_found) == 0:
            return None
        return ";".join(filter(
            lambda item_owner: item_owner != "root",
            map(lambda item_owner: item_owner.strip().replace("tdw_", ""),
                lst_found)
        )).strip(";")


    def __parse_partition_field(self, meta_info):
        """

        :param raw_info:
        :return:
        """
        pattern = r"parKey:FieldSchema\(name:([a-zA_Z0-9_]+),\stype:([a-zA_Z0-9_]+),\s"
        lst_found = re.findall(pattern, meta_info)
        if len(lst_found) == 0:
            return None
        elif len(lst_found) >= 1:
            return lst_found[0][0]
