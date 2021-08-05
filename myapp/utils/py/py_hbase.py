# -*- coding: utf-8 -*-
# 使用hbase向数据库中添加数据,使用前需要启动hbase和thrift服务器
# 启动hbase在cd /usr/local/hbase/bin/;start-hbase.sh   默认端口为60000，信息端口为60010
# 启动thrift服务器cd /usr/local/hbase/bin;hbase-daemon.sh start thrift   默认端口为9090


from thrift.transport import TSocket,TTransport
from thrift.protocol import TBinaryProtocol
from hbase import Hbase

# 这是一个redis常规操作的类.  里面定义了一些redis数据库的增删查改函数
import logging,json
import traceback

from hbase.ttypes import ColumnDescriptor
from hbase.ttypes import Mutation, BatchMutation
from common.config import *


# hbase中列族的属性
ColumnDescriptor_Atttr = ['name', 'maxVersions', 'compression', 'inMemory', 'bloomFilterType', 'bloomFilterVectorSize',
                          'bloomFilterNbHashes','blockCacheEnabled', 'timeToLive']


# 返回值全部自定义，可序列化。
class PyHbase(object):

    # 初始化,创建一个hbase客户端
    def __init__(self,thrift_ip=THRIFT_SERVER_IP,thrift_port=THRIFT_SERVER_PORT,raise_exception=False):
        self.exception = raise_exception      # 是否重新抛出异常
        # thrift默认端口是9090
        socket = TSocket.TSocket(thrift_ip, thrift_port)
        socket.setTimeout(5000)

        self.transport = TTransport.TBufferedTransport(socket)
        self.protocol = TBinaryProtocol.TBinaryProtocol(self.transport)
        self.client = Hbase.Client(self.protocol)
        # socket.open()
        self.transport.open()

    def deleteall(self,table_name):
        pass
        self.client.deleteAll(table_name)

    # 获取hbase某类型实例的所有属性转变为字典返回
    def attr_to_dict(self,hbase_obj,atrr_list):
        describe={}
        for attr in atrr_list:
            describe[attr] = hbase_obj.__getattribute__(attr)  # 获取实例对象属性的值
        return describe


    # 关闭链接。如果出现[Errno 32] Broken pipe，就要关闭通道重新启动
    def close(self):
        self.transport.close()

    # 获取所有表格信息
    def get_all_table(self,*args):
        try:
            alltable={}
            alltable_name = self.client.getTableNames()  # 获取所有表名
            for tablename in alltable_name:
                table={}
                allcf = self.client.getColumnDescriptors(tablename)  # 获取表的所有列族
                allcf_back = {}
                for columncf_name in allcf:
                    allcf_back[columncf_name] = allcf[columncf_name].__dict__

                table['ColumnDescriptors']=allcf_back
                allregions = self.client.getTableRegions(tablename)  # 获取所有与表关联的regions
                allregions_back=[]
                for region in allregions:
                    allregions_back.append(region.__dict__)
                table['TableRegions'] = allregions_back
                alltable[tablename]=table
            # print('所有表格', alltable)
            return alltable
        except Exception as e:
            logging.error('py_hbase get_all_table error: %s'%e)
            if(self.exception):
                raise e          # 抛出异常让外部处理
        return None

    # 获取表格列族信息
    def get_cf(self,table_name,*args):
        try:
            allcf = self.client.getColumnDescriptors(table_name)
            allcf_back = {}
            for columncf_name in allcf:
                allcf_back[columncf_name] = allcf[columncf_name].__dict__
            return allcf_back
        except Exception as e:
            if (self.exception):
                raise e  # 抛出异常让外部处理
            logging.error('get_cf error: %s' % e)
        return None

    # 创建表格。all_columnFamily_name为['cf1','cf2']的形式
    def creat_table(self,table_name,all_columnFamily_name,*args):
        try:
            table_column=[]
            for columnFamily in all_columnFamily_name:
                column = ColumnDescriptor(name=columnFamily)  # 定义列族
                table_column.append(column)
            self.client.createTable(table_name,table_column)  # 创建表
            # logging.info('creat table %s'%table_name)
            return True
        except Exception as e:
            if (not self.client.isTableEnabled(table_name)):  # 如果存在，并且禁用了就启动他
                self.client.enableTable(table_name)
            if (self.exception):
                raise e  # 抛出异常让外部处理
            logging.error('creat table error: %s' % e)  # 可能已经存在了
            return False


    # 删除表格
    def delete_table(self, table_name,*args):
        try:
            if (self.client.isTableEnabled(table_name)):
                self.client.disableTable(table_name)
                logging.info('disable table '+table_name)
            logging.info('disable table')
            self.client.deleteTable(table_name)  # 删除表.必须确保表存在,且被禁用
            logging.info('delete table'+table_name)
            return True
        except Exception as e:
            if (self.exception):
                raise e  # 抛出异常让外部处理
            logging.error('delete table error: %s' % e)
            return False


    # 启用表格
    def enable_table(self,table_name,*args):
        try:
            # 验证表是否被启用
            if (not self.client.isTableEnabled(table_name)):
                self.client.enableTable(table_name)  # 启用表
            return True
        except Exception as e:
            if (self.exception):
                raise e  # 抛出异常让外部处理
            logging.error('enable_table error: %s' % e)
            return False

    # 禁用表格
    def disable_table(self, table_name,*args):
        try:
            # 验证表是否被启用
            if (self.client.isTableEnabled(table_name)):
                self.client.disableTable(table_name)  # 禁用表
            return True
        except Exception as e:
            if (self.exception):
                raise e  # 抛出异常让外部处理
            logging.error('disable_table error: %s' % e)
            return False


    # 插入一行或之前一行的一个新版本   data是一个{'cf:column':value}的字典，value为可序列化对象，因为只能存储字节数组
    def insert_row_data(self, table_name, row_key, data,*args):

        allmutation = []
        for column in data:
            mutation = Mutation(column=column, value=json.dumps(data[column]))
            allmutation.append(mutation)

        if (len(allmutation) > 0):
            try:
                self.client.mutateRow(table_name,row_key,allmutation)  # 在表中执行一系列批次(单个行上的一系列突变)
                # logging.info('insert_row_data success')
                return True
            except Exception as e:
                if (self.exception):
                    raise e  # 抛出异常让外部处理
                logging.error('insert_row_data error: %s' % e)
                return False
        logging.info('insert data null')
        return False


    # 一次插入多行数据   data是一个{'row1':{'cf:column':value}}的字典
    def insert_rows_data(self,table_name,data):
        allmutation = []
        for row in data:
            if data[row]:
                one_row=[]
                for column in data[row]:
                    mutation = Mutation(column=column, value=json.dumps(data[row][column]))
                    one_row.append(mutation)
                batchMutation = BatchMutation(row,one_row)
                allmutation.append(batchMutation)

        if (len(allmutation) > 0):
            try:
                self.client.mutateRows(table_name,allmutation)
                return True
            except Exception as e:
                if (self.exception):
                    raise e  # 抛出异常让外部处理
                logging.error('insert_rows_data data error : %s' % e)
                return False
        logging.info('insert data null')
        return False

    # 插入和修改单元格数据，column为'cf:column'形式字符串，value为可序列化对象
    def insert_cell_data(self, table_name, row_key, column,value,*args):
        try:
            # 在hbase中全部都是字节流存储
            value = json.dumps(value)
            mutation = Mutation(column=column, value=value)
            self.client.mutateRow(table_name,row_key,[mutation])  # 在表中执行一系列批次(单个行上的一系列突变)
            # logging.info('insert cell data ')
            return True
        except Exception as e:
            if (self.exception):
                raise e  # 抛出异常让外部处理
            logging.error('insert_cell_data %s' % e)
        return False


    # 读取某一单元格最新数据,column为“cf:column1”类似格式
    def get_cell_data(self,table_name,row_key,column,*args):
        try:
            cells = self.client.get(table_name, row_key,column)
            # logging.info('get cell data success')
            cells_back=[]
            for cell in cells:
                cells_back.append(cell.__dict__)
            return cells_back
        except Exception as e:
            if (self.exception):
                raise e  # 抛出异常让外部处理
            logging.error('get cell data error: %s' % e)
            return None

    # 读取多列单元格最新的数据,columnlist为 ['cf1:a', 'cf2:a']类似列表
    def get_row_columns_data(self, table_name, row_key, columnlist,*args):
        try:
            # 获取指row_key指定列上的数据，不同时间戳下的多行记录
            row_result = self.client.getRowWithColumns(table_name,row_key,columnlist)  # 获取表中指定行与指定列在最新时间戳上的数据
            if (len(row_result) > 0):
                row = row_result[0]
                data = {}
                for column in row.columns:
                    data[column] = row.columns.get(column).value  # 只将最新的值返回
                return data
            return None
        except Exception as e:
            if (self.exception):
                raise e  # 抛出异常让外部处理
            logging.error('get mulcolumn data error :%s' % e)
            return None

    # 读取多列单元格指定时间戳以后的数据,columnlist为 ['cf1:a', 'cf2:a']类似列表
    def get_row_columns_data_ts(self, table_name, row_key, columnlist,timestamp,*args):
        try:
            # 获取指row_key指定列上的数据，不同时间戳下的多行记录
            row_result = self.client.getRowWithColumnsTs(table_name, row_key, columnlist,timestamp)  # 获取表中指定行与指定列在最新时间戳上的数据
            if (len(row_result) > 0):
                row = row_result[0]
                data = {}
                for column in row.columns:
                    data[column] = row.columns.get(column).value  # 只将最新的值返回
                return data
            return None
        except Exception as e:
            if (self.exception):
                raise e  # 抛出异常让外部处理
            logging.error('get mulcolumn data error :%s' % e)
            return None

    # 读取某一行数据,不存在table或row_key直接返回none
    def get_row_data(self, table_name, row_key,*args):
        try:
            row_result = self.client.getRow(table_name, row_key)  # result为一个列表，获取表中指定行在最新时间戳上的数据
            if(len(row_result)>0):
                row = row_result[0]
                data={}
                for column in row.columns:
                    data[column]=row.columns.get(column).value  # 只将最新的值返回
                return data
            return None
        except Exception as e:
            if (self.exception):
                raise e  # 抛出异常让外部处理
            logging.error('get row data error: %s' % e)
            return None

    # 读取某一行数据,不存在table或row_key直接返回none
    def get_row_data_ts(self, table_name, row_key,timestamp,*args):
        try:
            row_result = self.client.getRowTs(table_name, row_key,timestamp)  # result为一个列表，获取表中指定行在最新时间戳上的数据

            if (len(row_result) > 0):
                row = row_result[0]
                data = {}
                for column in row.columns:
                    data[column] = row.columns.get(column).value  # 只将最新的值返回
                return data
            return None
        except Exception as e:
            if (self.exception):
                raise e  # 抛出异常让外部处理
            logging.error('get row data error: %s' % e)
            return None

    # 删除指定表指定行与指定列的所有历史数据。column为'cf1:a'型字符串
    def del_cell_all(self,table_name,row_key,column,*args):
        try:
            self.client.deleteAll(table_name,row_key,column)
            logging.info('del cell all sucess')
            return True
        except Exception as e:
            if (self.exception):
                raise e  # 抛出异常让外部处理
            logging.error('del cell all error: %s' % e)
            return False

    # 删除指定表指定行与指定列中，小于等于指定时间戳的所有数据。column为'cf1:a'型字符串
    def del_cell_all_ts(self,table_name,row_key,column,timestamp,*args):
        try:
            self.client.deleteAllTs(table_name,row_key,column,timestamp)
            logging.info('del cell all ts sucess')
            return True
        except Exception as e:
            if (self.exception):
                raise e  # 抛出异常让外部处理
            logging.error('del cell all ts error: %s' % e)
            return False

    # 删除整行数据
    def del_row(self,table_name,row_key,*args):
        try:
            self.client.deleteAllRow(table_name,row_key)
            logging.info('del_row sucess')
            return True
        except Exception as e:
            if (self.exception):
                raise e  # 抛出异常让外部处理
            logging.error('del_row error: %s' % e)
            return False


    # 删除指定表指定行中，小于等于此时间戳的所有数据
    def del_row_ts(self,table_name,row_key,timestamp,*args):
        try:
            self.client.deleteAllRowTs(table_name,row_key,timestamp)
            logging.info('del_row_ts sucess')
            return True
        except Exception as e:
            if (self.exception):
                raise e  # 抛出异常让外部处理
            logging.error('del_row_ts error: %s' % e)
            return False


    # 锁定起止范围查询
    def scanner_rows_start_end(self,table_name,begin_row,end_row,select_column,num=-1,*args):

        scannerId = self.client.scannerOpenWithStop(table_name, begin_row,end_row, select_column)

        result=[]
        if(num>0):
            rowresults = self.client.scannerGetList(scannerId,num)
            if not rowresults:
                logging.info('scannerGetList no data')
                return result
            data = {}
            for item in rowresults:
                item_data = {}
                for column_name in item.columns:
                    item_data[column_name] = item.columns.get(column_name).value
                data[item.row] = item_data
            result.append(data)
        else:
            while True:
                rowresult = self.client.scannerGet(scannerId)
                if not rowresult:
                    break
                data = {}
                for item in rowresult:
                    item_data={}
                    for column_name in item.columns:
                        item_data[column_name] = item.columns.get(column_name).value
                    data[item.row]=item_data
                result.append(data)
        # 关闭扫描器
        self.client.scannerClose(scannerId)
        return result

    # 锁定开始范围查询。这样会遍历到结尾，比较耗时间
    def scanner_rows_start(self,table_name,begin_row,select_column,num=-1,*args):

        scannerId = self.client.scannerOpen(table_name, begin_row, select_column)

        result=[]
        if(num>0):
            rowresults = self.client.scannerGetList(scannerId,num)
            if not rowresults:
                logging.info('scannerGetList no data')
                return result
            data = {}
            for item in rowresults:
                item_data = {}
                for column_name in item.columns:
                    item_data[column_name] = item.columns.get(column_name).value
                data[item.row] = item_data
            result.append(data)
        else:
            while True:   # 会有很多数据
                rowresult = self.client.scannerGet(scannerId)
                if not rowresult:
                    break
                data = {}
                for item in rowresult:
                    item_data={}
                    for column_name in item.columns:
                        item_data[column_name] = item.columns.get(column_name).value
                    data[item.row]=item_data
                result.append(data)
        # 关闭扫描器
        self.client.scannerClose(scannerId)
        return result


if __name__ == "__main__":
    hbase = PyHbase('120.78.246.89','9090')
    print('connect')
    hbase.creat_table('test',['im','im1'])
    alltable = hbase.get_all_table()
    print(alltable)
    hbase.delete_table('test')













