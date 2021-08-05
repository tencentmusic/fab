# -*- coding: utf-8 -*-
import json
# import datetime
# import math
import os
import random
import base64
import numpy as np
# import subprocess
# import io
# import shutil
import threading
# import time
import argparse
from common.config import *
from common.util import *

# scp ES.py zhenghg@192.168.2.177:/home/luanpeng/virtual/elasticsearch/ES.py


endcommond =" > /dev/null 2>&1"  # 在命令后，使用这个命令可以防止输出内容过多的显示在屏幕上

class PyES():

    def __init__(self,url):
        self.url = url +"/"

    # 将base64字符串转化为浮点型列表
    def decode_float_list(self,base64_string):
        bytes = base64.b64decode(base64_string)
        return np.frombuffer(bytes, dtype=np.dtype('>f8')).tolist()

    # 讲浮点型列表转化为字符串
    def encode_array(self,arr):
        base64_str = base64.b64encode(np.array(arr).astype(np.dtype('>f8'))).decode("utf-8")
        return base64_str

    def make_index_data(self,index,type,id):
        dict={}
        dict["index"]={"_index":index,"_type": type,"_id":id}
        return dict

    # 产生a-b范围的随机数列表
    def make_rand_data(self,num,a,b):
        arr=[]
        for i in range(num):
            arr.append(random.uniform(a,b))    # 产生0-100之间的512维度的浮点数据。python浮点占8个字节，如果是512个字节，需要64维度
        return arr

    # 将列表转化为base64编码的字符串
    def make_base64(self,field_name, float_arr):
        base64_data = {}
        base64_data[field_name] = self.encode_array(float_arr)
        return base64_data

    # 产生批量导入文件.json格式，不要超过10M
    def make_base64_file(self,filenum,directory,index,type,field):
        if not os.path.exists(directory):  # 如果目录不存在
            os.makedirs(directory)  # 创建目录
        id = 0
        # 生成样本数据
        for file_id in range(0,filenum):
            filepath = directory+'/data'+str(file_id)+'.json'
            file=open(filepath,mode='w')
            for i in range(500):   # 每个json文件不能超过10m不然没法批量向elasticsearch中添加。整型数据1000条7m，浮点型数据500条7m
                file.writelines(json.dumps(self.make_index_data(index,type,id)))
                file.writelines("\n")
                file.writelines(json.dumps(self.make_base64(field,self.make_rand_data(512,0,100))))
                file.writelines("\n")
                id+=1
            file.close()
            print(filepath,'文件写入完成')



    # 将文件批量上传到ES
    def import_data_from_file(self,filenum,directory):
        # 调用sh文件，讲样本数据导入到elasticsearch
        # backstr = os.system('sh /home/luanpeng/python/elasticsearch/bat.sh')    # os.popen(cmd):返回输出内容
        # print(backstr)

        # # 或者直接执行sh命令
        for file_id in range(filenum):
            command_line = 'curl -XPUT '+self.url+'_bulk?pretty --data-binary @'+directory+'/data' + str(file_id) + '.json'
            # print('命令行',command_line)
            status = os.system(command_line+endcommond)  # os.popen(cmd):返回输出内容，os.system返回状态码。现在每次导入都会更新数据
            if (status == 0):
                print(file_id, '批量导入数据成功')
            else:
                print(file_id, '批量导入数据失败')

    # 创建index
    def add_index(self,index):
        #### =======创建index===========
        command_line = "curl -XPUT '"+self.url+index+"?pretty'"
        # print(command_line)
        status = os.system(command_line+endcommond)
        if (status == 0):
            print('创建index成功')
        else:
            print('创建index失败')

    # 添加映射，设置index、type、field的特征
    def add_mapping(self,index,type,change_mapping_data):
        commanstr = "curl -XPOST '"+self.url+index+'/'+type+"/_mapping?pretty'" + " -d '" + json.dumps(change_mapping_data) + "'"+endcommond
        # print('命令行',commanstr)

        status = os.system(commanstr)  # os.popen(cmd):返回输出内容，os.system返回状态码。现在每次导入都会更新数据
        if (status == 0):
            print('映射成功')
        else:
            print('映射失败')

    # 读取映射
    def get_mapping(self,index):
        # 查看索引map
        commanstr = "curl -XGET '" + self.url + index + "/_mapping?pretty'"
        status = os.popen(commanstr)  # os.popen(cmd):返回输出内容，os.system返回状态码。现在每次导入都会更新数据
        result = status.read()
        status.close()
        print('映射：',result)
        return result


    # 删除idnex，如果要删除所有数据，index=*
    def remove_index(self,index):
        # 调用命令删除数据
        status = os.system('curl -XDELETE localhost:9200/'+index+'?pretty'+endcommond)  # os.popen(cmd):返回输出内容，os.system返回状态码
        if (status == 0):
            print('删除index成功')
        else:
            print('删除index失败')

    # 根据id查询字段
    def get_field(self,index,type,id):
        process = os.popen('curl '+self.url+index+"/"+type+'/'+str(id)+'?pretty=true')   # 查询一个记录试试
        output = process.read()
        process.close()
        print(output)
        output = json.loads(output)
        print(output)
        return output
        # data_list = decode_float_list(json.loads(output)['_source']['embedding_vector'])
        # print('查看数据',data_list)
        # return data_list

    # 添加一条记录
    def add_field(self,index,type,field,value):
        return True

    # 查找距离最近的向量
    def knn(self,index=None,type=None,field=None,arr=None,k=1):
        return 1,arr
        query = {
            "query": {
                "function_score": {
                    "boost_mode": "replace",
                    "script_score": {
                        "script": {
                            "inline": "binary_vector_score",
                            "lang": "knn",
                            "params": {
                                "cosine": False,  # 为false表示使用点乘， 为true表示使用余弦相似
                                "field": field,
                                "vector": arr
                            }
                        }
                    }
                }
            },
            "size": k
        }


        # query ={
        #     "query": {"match_all": {}},
        #     "from":9995,
        #     "size": 6
        # }
        #
        linuxcommand = "curl '"+self.url+index+"/_search?pretty' -d '" + json.dumps(query) + "'"
        # linuxcommand = "curl 'localhost:9200/user/icon/_search?pretty'"
        # print('命令行',linuxcommand)

        back = os.popen(linuxcommand).read()  # 查询一个记录试试
        back = json.loads(back)
        # print(back)
        print('耗费时间：',back['took'],'ms')
        dataarr = back['hits']['hits']
        alluser=[]
        for temp in dataarr:
            user={}
            user['id'] = temp['_id']
            user['data']=self.decode_float_list(temp['_source'][field])
            alluser.append(user)
            # print('用户id：',user['id'],',',user['data'])
        return alluser

    def knn_local(self,alluser,user):
        alluser_mat = np.array(alluser)
        user_mat = np.array(user).repeat(-1,1)
        result = np.dot(alluser_mat,user_mat)

        maxuser = np.where(np.max())







table_filenum=100   # 一个文件是500个记录，一个表用100个文件的数据，也就是5万个记录
tablenum=180    # 使用180个表格存储。每个表5万，共900万记录
index_src = 'user'
type_src='icon'
field_src='column'
if __name__=="__main__":
    parser = argparse.ArgumentParser(description='es do something')
    parser.add_argument('--makefile',default=False, action='store_true', help=('make file to insert database'))
    parser.add_argument('--delindex',default=False, action='store_true', help='delete index')
    parser.add_argument('--importfile',default=False, action='store_true', help='import file to database')
    parser.add_argument('--tablenum', default=10, help=('import file to insert database'))
    parser.add_argument('--es',default=False, action='store_true', help='import file to database')

    args = vars(parser.parse_args())
    # shutil.rmtree('data')    # 递归删除整个文件夹
    es = PyES('127.0.0.1:9200')
    if(args['makefile']):   # 如果命令中要产生文件
        for i in range(tablenum):   # 根据文件数目批量产生文件。每个文件500个记录,每个表100个文件，也就是5万记录，60个表是300万记录
            es.make_base64_file(table_filenum,'data/data'+str(i),index_src+str(i),type_src+str(i),field_src+str(i))   # 生成批量文件，# 每100个文件的数据存储在一个表格中。

    if (args['delindex']):  # 如果命令中要删除index
        es.remove_index('*')  # 删除index
        for i in range(tablenum):
            index=index_src+str(i)
            type=type_src+str(i)
            field=field_src+str(i)
            change_mapping_data = {
                type: {  # type名称
                    "properties": {
                        field: {  # 字段名称
                            "type": "binary",
                            "doc_values": True
                        }
                    }
                }
            }

            es.add_index(index)   # 添加idnex
            es.add_mapping(index,type,change_mapping_data)   # 添加映射，设置字段特征
            es.get_mapping(index)   # 查看映射的添加情况

    if (args['importfile']):  # 如果命令中要删除index
        for i in range(110,int(args['tablenum'])):
            es.import_data_from_file(table_filenum,'data/data'+str(i))
    # es.get_field(index,type,id=502)  # 根据id查询field的值


    def knn(data_list,i):
        # 使用插件快速查询knn
        alluser = es.knn(index_src+str(i),type_src+str(i),field_src+str(i),data_list,1)   # 快速查找knn
        # print(alluser)

    if(args['es']):
        data_list = es.make_rand_data(512, 0, 100)  # 产生一个随机数据
        tablenum = int(args['tablenum'])
        for i in range(tablenum):
            group = tablenum/60   # 每次只能同时查询300万记录,耗时1.5s
            t = threading.Thread(target=knn, args=(data_list,i))
            t.start()

















