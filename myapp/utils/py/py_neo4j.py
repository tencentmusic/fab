# -*- coding:utf-8 -*-

from neo4j.v1 import GraphDatabase
import requests
import datetime,time

class Neo4j_client():

    @ staticmethod
    def find_leader(neoj4_http_hosts,username='neo4j',password='admin'):
        for host in neoj4_http_hosts:
            res = requests.request('GET', host+'/db/manage/server/core/writable',auth=(username,password))
            leader = res.json()
            if leader:
                print(host)
                return host
        return None


    def __init__(self,neoj4_host,username='neo4j',password='admin'):
        self.driver = GraphDatabase.driver(neoj4_host,auth=(username, password))
        # def test(tx):
        #     command = 'merge (n:test{name:$name}) ON MATCH SET n.update_time=$update_time return n'
        #     node = tx.run(command,name='test',update_time=int(time.time()))
        #     return node.data()
        # node = self.driver.session().write_transaction(test)


    def close(self):
        self.driver.close()

    # 创建name唯一性，name是profile_id
    def create_name_unique(self,tx,project):
        command = 'CREATE CONSTRAINT ON (n:%s) ASSERT n.name IS UNIQUE'%project
        tx.run(command)
        return None

    # 删除一个项目的全部节点和边
    def clear_all(self,tx,project):
        command = 'MATCH (n:%s) DETACH DELETE n' % project
        tx.run(command)
        return None

    # 建节点，原节点没有就会建，属性和属性的值完全一样才会保留原数据
    def create_node(self,tx,project,profile_id,update_time):
        tx.run("MERGE (node: %s{name: $profile_id, project: $project,update_time: $update_time}) "%project,profile_id=profile_id,project=project,update_time=update_time)
        return None

    # 删除节点和关联的边
    def delete_node_from_profile_id(self,tx,project,profile_id):
        tx.run("MATCH (node: %s{name: $profile_id, project: $project}) DETACH DELETE node "%project,profile_id=profile_id,project=project)
        return None

    # 删除节点和关联的边
    def delete_node_from_update_time(self,tx,project,update_time):
        tx.run("MATCH (node: %s{project: $project}) WHERE node.update_time<$update_time DETACH DELETE node "%project,update_time=update_time,project=project)
        return None


    # 建立节点之间的连边，这个是单向的，里面的count是边的属性，边可以有多个属性。
    def create_relationship(self,tx, project, profile_id, neighbor_id, peer_count,update_time):
        tx.run("MATCH (from: %s{name: $profile_id}),(to: %s{name: $neighbor_id}) "%(project,project)+
               "MERGE (from)-[:peer{peer_count:$peer_count,update_time:$update_time}]->(to) ",
               profile_id=profile_id,neighbor_id=neighbor_id,peer_count=peer_count,update_time=update_time)
        return None

    # 删除指定时间范围之前的关系
    def delete_relations_from_update_time(self,tx,project,update_time):
        tx.run("MATCH (node1:%s) -[r]-(node2:%s) WHERE r.update_time<$update_time DELETE r" % (project,project),update_time=update_time, project=project)
        return None


    # 根据档案号读取node
    def get_node_from_profile_id(self,tx,project, profile_id):
        nodes = tx.run("MATCH (node:%s {name: $name}) RETURN node"%project, name=profile_id)
        profile = nodes.single()[0]
        result = {'id': profile.id, 'profile_id': profile.get('name'), 'project': profile.get('project'),
                  'labels': list(profile.labels)}
        return result

    # 读取邻接点和边，关系方向为当前节点到邻接点
    def get_neighbors_relations(self,tx,project,profile_id):
        results = tx.run("MATCH (src_node:%s {name: $profile_id})-[relation:peer]->(neighbor) RETURN relation,neighbor"%project, profile_id=profile_id)
        results = results.data()
        # print(results)
        neighbors={}  # {id:{"node":{},"relation":{}}}
        for result in results:
            # print(result)
            relation = result['relation']
            neighbor=result['neighbor']
            neighbors[neighbor.id]={
                'node':{'id':neighbor.id,'name':neighbor.get('name'),'project':neighbor.get('project'),'labels':list(neighbor.labels)},
                'relation':{'id':relation.id,'type':relation.type,'peer_count':relation.get('peer_count'),'update_time':relation.get('update_time')}
            }
            # print(relation)
            # print(neighbor)
        # print(neighbors)
        return neighbors



    # 同时创建或更新所有邻节点和关系。neighbors是列表形式[{profile_id:profile_id,peer_count:peer_count}]
    def update_neighbors(self,tx, project, src_profile_id, neighbors,update_time):
        # print(src_profile_id,neighbors)
        command = '''
        MERGE (src_node:%s{name:$src_profile_id,project: $project})
        WITH src_node
        UNWIND $peer_profiles AS peer_profile
        MERGE (peer_node:%s { name: peer_profile.profile_id,project: $project})
        MERGE (src_node)<-[r:peer]-(peer_node)
        ON CREATE SET r.update_time=$update_time,r.peer_count=peer_profile.peer_count
        ON MATCH SET (CASE WHEN r.update_time < $update_time THEN r END ).peer_count=peer_profile.peer_count+r.peer_count,r.update_time=$update_time
        '''%(project,project)
        # print(command)
        tx.run(command,project=project,peer_profiles=neighbors,src_profile_id=src_profile_id,update_time=update_time)
        return None


    # 将一个节点的全部关系转移到另一个节点上，并删除原节点
    def move_node(self,tx,project,src_profile_id,des_profile_id):
        # print(src_profile_id,des_profile_id)
        # 匹配不定方向，会把双边方向都匹配下来, 由由于原邻接点需要与目标节点建立双边关系，所以如果原关系取双边的话，会重复计算一遍
        command = '''
                MATCH (src_node:%s { name: $src_profile_id })-[src_r:peer]->(peer_node),(des_node:%s { name: $des_profile_id }) WHERE NOT id(peer_node)=id(des_node)
                MERGE (des_node)-[des_r:peer]-(peer_node)
                ON CREATE SET des_r.update_time=src_r.update_time,des_r.peer_count=src_r.peer_count
                ON MATCH SET des_r.peer_count=src_r.peer_count+des_r.peer_count
                DETACH DELETE src_node''' % (project, project)
        # print(command)
        tx.run(command,src_profile_id=src_profile_id,des_profile_id=des_profile_id)
        # print(result.data())
        return None







if __name__=='__main__':
    # 先查看那个是leader
    hosts = {
        'http://192.168.11.127:30474':'bolt://192.168.11.127:30687',
        'http://192.168.11.127:31474': 'bolt://192.168.11.127:31687',
        'http://192.168.11.127:32474': 'bolt://192.168.11.127:32687',
    }
    leader_host  = Neo4j_client.find_leader(list(hosts.keys()),username='neo4j',password='admin')
    neo4j_client = Neo4j_client(neoj4_host=hosts[leader_host])
    # neo4j_client.driver.session().write_transaction(neo4j_client.clear_all, 'test')   # 删除yinli的全部节点和边
    # neo4j_client.driver.session().write_transaction(neo4j_client.create_name_unique, 'test')   # 创建name唯一性。
    peer={
        'lp1':{
            'lp2':3,
            'lp3':4
        },
        'lp2':{
            'lp1':3,
            'lp3':1
        },
        'lp3':{
            'lp1':4,
            'lp2':1
        }
    }

    # 创建或者更新节点和关系
    for src_profile_id in peer:
        neighbors = peer[src_profile_id]
        new_neighbors=[]
        for neighborid in neighbors:
            new_neighbors.append({'profile_id':neighborid,'peer_count':neighbors[neighborid]})
        print(new_neighbors)
        neo4j_client.driver.session().write_transaction(neo4j_client.update_neighbors, 'test', src_profile_id, new_neighbors, int(time.time()))

    #
    # # 读取节点
    # profile = neo4j_client.driver.session().write_transaction(neo4j_client.get_node_from_profile_id, 'yinli','lp1')
    # print(profile)
    #
    # # 读取节点的邻接点和边
    # neighbors = neo4j_client.driver.session().write_transaction(neo4j_client.get_neighbors_relations,'yinli', 'lp1')
    # print(neighbors)
    #
    # # 转移节点
    # neo4j_client.driver.session().write_transaction(neo4j_client.move_node,'yinli', 'lp1','lp2')
    #
    # # 删除节点和关联的边关系
    # neo4j_client.driver.session().write_transaction(neo4j_client.delete_node_from_profile_id, 'yinli','lp2')




