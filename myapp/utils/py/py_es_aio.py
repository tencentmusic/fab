
import asyncio
import json
# pip install elasticsearch-async
from elasticsearch_async import AsyncElasticsearch

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
    # 初始化hosts是list,每个参数都是为一个"192.168.11.127:9200",
    def __init__(self,hosts,loop):
        self.hosts = hosts
        self.timeout=5
        # self.es = Elasticsearch(hosts,maxsize=maxsize,sniff_on_start=sniff_on_start,sniff_on_connection_fail=sniff_on_connection_fail,sniffer_timeout=sniffer_timeout, timeout=self.timeout)
        self.es = AsyncElasticsearch(hosts=self.hosts)
        self.es.transport.loop=loop

    async def print_info(self):
        info = await self.es.info()
        print(info)

    # 创建索引
    async def index_create(self,index,body=None,params=None):

        # 创建索引，不忽略 400 错误．这个是index已存在产生的
        if body and params:
            return await self.es.indices.create(index=index,body=body,params=params)
        elif body:
            return await self.es.indices.create(index=index, body=body)
        elif params:
            return await self.es.indices.create(index=index, params=params)
        else:
            return await self.es.indices.create(index=index)

    # 获取索引信息
    async def index_get(self,index):
        return await self.es.indices.get(index=index)
    # 刷新索引
    async def index_refresh(self,index):
        await self.es.indices.refresh(index=index)
    # 将索引转移到另一个索引上
    async def reindex(self,source,dest):
        await self.es.reindex(body={'source':source,"dest":dest})
    # 更新index的setting
    async def index_update_settings(self,index,settings):
        return await self.es.indices.put_settings(index=index,body=settings)   # 因为参数是list,或者*,所以加了一层[]
    # 更新index的mapping
    async def index_update_mappings(self, index,doc_type,mappings):
        return await self.es.indices.put_mapping(index=index,doc_type=doc_type,body=mappings)  # 因为参数是list,或者*,所以加了一层[]
    # 删除索引
    async def index_delete(self,index):
        return await self.es.indices.delete(index=[index])   # 因为参数是list,或者*,所以加了一层[]
    # 创建更新数据
    async def document_index(self,index,doc_type,id,body):
        return await self.es.index(index=index, doc_type=doc_type, id=id, body=body)
    # 更新数据
    async def document_update(self,index,doc_type,id,body):
        return await self.es.update(index=index, doc_type=doc_type, id=id, body=body)
    # 读取数据
    async def document_get(self,index,doc_type,id):
        return await self.es.get(index=index, doc_type=doc_type, id=id)
    # 批量数据
    async def document_gets(self, index, doc_type, body):
        return await self.es.mget(index=index, doc_type=doc_type, body=body)
    # 插入数据
    async def document_delete(self,index,doc_type,id):
        return await self.es.delete(index=index, doc_type=doc_type, id=id)

    # 批量插入,action = [{'_index': 'test-index', '_type': 'tweet', '_id': i, '_source': doc} for i in range(1, 10)]
    async def document_bulk(self,index,doc_type,body):
        return await self.es.bulk(index=index,doc_type=doc_type,body=body)
        # return helpers.bulk(self.es, action)
    # 搜索
    async def document_search(self,index,body,**args):
        # print(index,body,args)
        res = await self.es.search(index=index, body=body,**args)
        # print(res)
        return res

    # 搜索
    async def document_search_update(self,index,body,**args):
        res = await self.es.update_by_query(index=index, body=body,**args)
        return res

    # 搜索
    async def document_search_delete(self,index,body,**args):
        res = await self.es.delete_by_query(index=index,body=body,**args)
        return res




if __name__ == '__main__':

    host = ["192.168.11.127:31001"]
    loop = asyncio.get_event_loop()
    es=ES(host,loop)
    # tasks=[es.print_info(),es.index_delete("test")]
    query={
        "body": {
            "query": {
                "match_all": {}
            },
            # "sort": [
            #     {
            #         "update_time": {
            #             "order": "desc",
            #             "missing": "_last"
            #         }
            #     }
            # ],
        },
        "size": 5,
        "from": 0
    }
    tasks1 = [es.document_search("test",query["body"],size=query["size"],from_=query["from"])]
    # data={}
    # data['body']={
    #     "create": [
    #         {
    #             "id": "14",
    #             "name": "栾鹏",
    #             "group": "印力集团",
    #             "user_type": "automatic",
    #             "gender": "male",
    #             "age": 14,
    #             "phone": "16656896548",
    #             "id_card": "85625633212145663325",
    #             "address": "深圳市南山区德馨花园"
    #         }
    #     ]
    # }

    # 重新构造请求体
    # body = []
    # for key in data['body']:
    #     if type(data['body'][key]) == list:
    #         for one_data in data['body'][key]:
    #             deal_dict = {
    #                 key: {
    #                     "_id": one_data['id']
    #                 }
    #             }
    #             del one_data["id"]
    #             body.append(deal_dict)
    #             if one_data:
    #                 if key == 'update':
    #                     body.append({"doc": one_data})
    #                 elif key == 'create' or key == 'index':
    #                     body.append(one_data)
    #
    # print(body)
    # tasks1 = [es.document_bulk("test", doc_type='book',body=body)]

    loop.run_until_complete(asyncio.gather(*tasks1))
    loop.run_until_complete(es.es.transport.close())
    loop.close()
