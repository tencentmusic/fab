

# pip install elasticsearch
from elasticsearch import helpers
from elasticsearch import Elasticsearch
import json


# 人性化输出
def printf(data):

    if type(data) == bytes:
        print(json.loads(json.dumps(data.decode('utf-8'), indent=4)))
    if type(data) == str:
        print(json.loads(json.dumps(data, indent=4)))
    if type(data) == dict:
        print(data)

# es的公共基础类
class ES():
    # 初始化hosts是list,每个参数都是为一个{"host": "192.168.11.127","port": 31001},
    def __init__(self,hosts,maxsize=25,sniff_on_start=True,sniff_on_connection_fail=True,sniffer_timeout=60):
        self.hosts = hosts
        self.timeout=5
        # self.es = Elasticsearch(hosts,maxsize=maxsize,sniff_on_start=sniff_on_start,sniff_on_connection_fail=sniff_on_connection_fail,sniffer_timeout=sniffer_timeout, timeout=self.timeout)
        self.es = Elasticsearch(hosts)

    def help(self):
        import requests
        res = requests.get('http://'+self.hosts[0]['host']+":"+str(self.hosts[0]['port']))
        printf(res.content)

    # 创建索引
    def index_create(self,index,body=None,params=None):
        # 创建索引，不忽略 400 错误．这个是index已存在产生的
        if body and params:
            return self.es.indices.create(index=index,body=body,params=params)
        elif body:
            return self.es.indices.create(index=index, body=body)
        elif params:
            return self.es.indices.create(index=index, params=params)
        else:
            return self.es.indices.create(index=index)

    # 获取索引信息
    def index_get(self,index):
        return self.es.indices.get(index=index)
    # 刷新索引
    def index_refresh(self,index):
        self.es.indices.refresh(index=index)
    # 将索引转移到另一个索引上
    def reindex(self,source,dest):
        self.es.reindex(body={'source':source,"dest":dest})
    # 更新index的setting
    def index_update_settings(self,index,settings):
        return self.es.indices.put_settings(index=index,body=settings)   # 因为参数是list,或者*,所以加了一层[]
    # 更新index的mapping
    def index_update_mappings(self, index,doc_type,mappings):
        return self.es.indices.put_mapping(index=index,doc_type=doc_type,body=mappings)  # 因为参数是list,或者*,所以加了一层[]
    # 删除索引
    def index_delete(self,index):
        return self.es.indices.delete(index=[index])   # 因为参数是list,或者*,所以加了一层[]
    # 创建更新数据
    def document_index(self,index,doc_type,id,body):
        return self.es.index(index=index, doc_type=doc_type, id=id, body=body)
    # 更新数据
    def document_update(self,index,doc_type,id,body):
        return self.es.update(index=index, doc_type=doc_type, id=id, body=body)
    # 读取数据
    def document_get(self,index,doc_type,id):
        return self.es.get(index=index, doc_type=doc_type, id=id)
    # 批量数据
    def document_gets(self, index, doc_type, body):
        return self.es.mget(index=index, doc_type=doc_type, body=body)
    # 插入数据
    def document_delete(self,index,doc_type,id):
        return self.es.delete(index=index, doc_type=doc_type, id=id)

    # 批量插入,action = [{'_index': 'test-index', '_type': 'tweet', '_id': i, '_source': doc} for i in range(1, 10)]
    def document_bulk(self,index,doc_type,body):
        return self.es.bulk(index=index,doc_type=doc_type,body=body)
        # return helpers.bulk(self.es, action)
    # 搜索
    def document_search(self,index,body,**args):
        res = self.es.search(index=index, body=body,**args)
        return res

    # 搜索
    def document_search_update(self,index,body,**args):
        res = self.es.update_by_query(index=index, body=body,**args)
        return res

    # 搜索
    def document_search_delete(self,index,body,**args):
        res = self.es.delete_by_query(index=index,body=body,**args)
        return res




if __name__ == '__main__':

    host = {
        "host": "192.168.11.127",
        "port": 31001
    }
    es_client=ES(host)
    # tasks=[es.print_info(),es.index_delete("test")]
    query={
        "body": {
            "query": {
                "match_all": {}
            },
            "sort":[
                {
                    "update_time": {
                        "order": "desc",
                        "missing": "_last"
                    }
                }],
        },

        "size": 5,
        "from": 0
    }
    result = es_client.es.search(index="test", body=query["body"],size=query["size"],from_=query["from"])
    print(result)

