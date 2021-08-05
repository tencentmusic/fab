# coding: utf-8
import happybase
import logging
from common.config import *
import json

# 替换hbase和ttype文件



class Hbase(object):
    """
     :param str name:table name
     :param str row: the row key
     :param list_or_tuple columns: list of columns (optional)
    """
    # 模式直接使用一个连接
    def __init__(self,host=THRIFT_SERVER_IP,port=THRIFT_SERVER_PORT,timeout = 60*1000):
        port=int(port)
        self.host = host
        self.port=port
        self.timeout=timeout
        self.conn = happybase.Connection(host, port=port, autoconnect=True,timeout=timeout)
        self.conn.open()

    # 创建连接词,先关闭conn
    def make_pool(self,size=3):
        try:
            self.conn.close()
        except Exception as e:
            print(e)
        self.pool = happybase.ConnectionPool(size=size, host=self.host, port=self.port, autoconnect=True)
    # 获取连接池中的连接
    def get_connect(self):
        with self.pool.connection() as self.conn:
            pass
        # self.conn= self.pool.connection(timeout=5)    # 只是获取并不能保证连接已经失去了连续，需要在

    # 刷新连接
    def refresh_connect(self):
        try:
            self.conn.close()
        except Exception as e:
            print(e)
        self.conn = happybase.Connection(self.host, port=self.port, autoconnect=True, timeout=self.timeout)
        self.conn.open()



    def disable(self, table_name,*args):
        if self.conn.is_table_enabled(table_name):
            self.conn.disable_table(table_name)

    def enable(self, table_name,*args):
        if not self.conn.is_table_enabled(table_name):
            self.conn.enable_table(table_name)

    def list_tables(self,*args):
        tabels = self.conn.tables()
        return tabels

    def table(self, table_name,*args):
        table = self.conn.table(table_name)
        return table

    def create(self, table_name, family_column,*args):
        """
        :param name: str
        :param kw: dict
        exp:
            kw = {"":dict()}
        :return: None
        """
        families = {}
        if (type(family_column) == dict):
            families = family_column
        if (type(family_column) == list):
            for item in family_column:
                families[item] = dict()
        try:
            self.conn.create_table(table_name, families)
        except Exception as e:
            print(e)
    # 删除表
    def drop(self, table_name,*args):
        try:
            self.conn.disable_table(table_name)
        except Exception as e:
            print(e)
        try:
            self.conn.delete_table(table_name)
        except Exception as e:
            print(e)



    # 删除行
    def delete(self, table_name, row_key,*args):
        table = self.table(table_name)
        table.delete(row_key)

    # 批量删除行,rows_key是list
    def deletes(self, table_name, rows_key,*args):
        bat = self.table(table_name).batch()
        for row_key in rows_key:
            bat.delete(row_key)
        bat.send()


    # 删除指定时间范围的数据
    def deletes_row_range(self, table_name, start_row_key,end_row_key,*args):
        nu_generator = self.table(table_name).scan(row_start=start_row_key, row_stop=end_row_key)  # 返回一个迭代器
        bat = self.table(table_name).batch()
        # 循环:
        try:
            for i in range(0,1000):
                row_key = next(nu_generator)
                bat.delete(row_key[0])
        except StopIteration:
            # 遇到StopIteration就退出循环
            print('data finish')
        finally:
            bat.send()



    def delete_column(self, table_name, row_key, columns,*args):
        self.table(table_name).delete(row_key, columns=columns)


    def cell(self, table_name, row_key, column,*args):
        """
        :return: list
        """
        return self.table(table_name).cells(row_key, column)

    def families(self, table_name,*args):
        """
        :return: dict
        """
        return self.conn.table(table_name).families()

    # data是字典类型
    def put(self, table_name, row_key, row_data,*args):
        if row_data:
            self.table(table_name).put(row_key, row_data)
            return True
        else:
            return False

    # rows_data是字典{row_key1:row_data1,row_key2:row_data2,}
    def puts(self, table_name, rows_data, *args):
        if rows_data:
            bat = self.table(table_name).batch()
            for row_key in rows_data:
                if rows_data[row_key]:
                    bat.put(row_key, rows_data[row_key])
            bat.send()
            return True
        else:
            return None

    # 注意 兼容性,之前使用的是row_key
    def get(self, table_name, row_key=None,row=None,columns=None,*args):
        if row:
            return self.table(table_name).row(row,columns=columns)
        elif row_key:
            return self.table(table_name).row(row_key,columns=columns)

    # 读取多行
    def gets(self, table_name, row_keys=None,columns=None,*args):
        if row_keys:
            return self.table(table_name).rows(row_keys,columns=columns)


    def scan(self, table_name,begin=None,end=None,columns=None,limit=None,reverse=False,*args):
        if limit:
            limit=int(limit)
        if type(columns)==str:
            columns=[columns]
        if columns:
            if not begin:
                nu = self.conn.table(table_name).scan(columns=columns,limit=limit,reverse=False)
            elif not end:
                nu = self.conn.table(table_name).scan(row_start=begin,columns=columns,limit=limit,reverse=False)
            else:
                nu = self.conn.table(table_name).scan(row_start=begin,row_stop=end,columns=columns,limit=limit,reverse=False)
        else:
            if not begin:
                nu = self.conn.table(table_name).scan(limit=limit,reverse=False)
            elif not end:
                nu = self.conn.table(table_name).scan(row_start=begin,limit=limit,reverse=False)
            else:
                nu = self.conn.table(table_name).scan(row_start=begin,row_stop=end,limit=limit,reverse=False)

        datasets = {}
        for row in nu:
            datasets[row[0].decode('utf-8')]=row[1]
        return datasets

    # 目前调试不通
    def scan_prefix(self, table_name,prefix,columns=None,*args):
        if type(prefix)!=bytes:
            prefix=bytes(prefix,encoding='utf-8')
        if columns:
            nu = self.conn.table(table_name).scan(row_prefix=prefix,columns=columns)
        else:
            nu = self.conn.table(table_name).scan(row_prefix=prefix)

        datasets = {}
        # print(nu)
        for row in nu:
            # print(row)
            datasets[row[0].decode('utf-8')]=row[1]
        return datasets


    # 将scan查询的数据集，转化为json
    def dateset_to_json(self,datasets,to_json=True):
        back_datas={}
        for row_key in datasets:
            row = datasets[row_key]
            back_data={}
            for attr in row:
                if to_json:
                    back_data[attr.decode('utf-8')]=json.loads(row[attr].decode('utf-8'))
                else:
                    back_data[attr.decode('utf-8')] = row[attr].decode('utf-8')
            back_datas[row_key]=back_data
        return back_datas


    def incr(self, table_name, row, column,*args):
        self.table(table_name).counter_inc(row, column=column)

    def dec(self, table_name, row, column,*args):
        self.table(table_name).counter_dec(row, column=column)




    # 将key和value可能是bytes类型的转化为str
    def to_dict(self,data):
        if data:
            if type(data)==int: return data
            if type(data)==bytes: return data.decode('utf-8')
            if type(data)==str: return data
            if type(data)==dict:
                back={}
                for key in data:
                    back[self.to_dict(key)]=self.to_dict(data[key])
                return back
            if type(data)==list or type(data)==tuple:
                back=[]
                for key in data:
                    back.append(self.to_dict(key))
                return back
        return None


    def close(self):
        self.conn.close()



if __name__ == "__main__":
    #client = Hbase(host="192.168.11.127", port=30036) #Hbase(host="39.108.150.8")
    client = Hbase(host="192.168.12.96", port=30036)  # Hbase(host="39.108.150.8")
    print(client)
    print(client.list_tables())
    col_family = {"im": {}}
    table_name = "vesionbook-device"
    #client.create(table_name, col_family)
    data = client.gets(table_name, ["10000_1545877443000000","10000_1545877443000000"])
    print(data)
    data=client.to_dict(data)
    print(data)
    # '''
    #print(client.get(table_name, "31b2d26abf7b21797871d5b232c91b5d"))
    # data = client.get(table_name, "c825dfd261007dd19ab92071e2a87cdc").get(b"im::image_data")
    #print(client.drop("face_image"))

    #print(client.list_tables())
    # result = client.scan("vesionbook-device",begin="camera_34118_1553689290053272",end="camera_34118_2553143466672832")
    # for key in result:
    #     print(key,result[key])
    #     break
    # print(len(client.scan("vesionbook-device")))