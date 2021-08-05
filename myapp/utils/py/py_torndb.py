
# 如果安装torndb,记得要替换/usr/local/lib/python3.6/dist-packages文件夹下的torndb.py文件,内容同utils/torndb-python3.py

import queue,threading,torndb

# mysql异步线程池
class MysqlConnPool(object):

    def __init__(self, host, database, user, pwd, max_conns=30):
        self.idle_conn = queue.Queue()
        self.pool_size = 0
        self.max_conns = max_conns
        self.conn_params = (host, database, user, pwd)
        self.poll_size_mutex = threading.Lock()

    def _get_conn_from_pool(self):
        if self.idle_conn.empty() and self.pool_size < self.max_conns:
            conn = torndb.Connection(*self.conn_params, time_zone="+8:00")
            self.poll_size_mutex.acquire()
            self.pool_size += 1
            self.poll_size_mutex.release()
            return conn
        return self.idle_conn.get()
    # 查询函数
    def query(self, sqlcommand,*args, **kwargs):
        conn = self._get_conn_from_pool()
        res = conn.query(sqlcommand,*args, **kwargs)
        self.idle_conn.put(conn)
        return res

    # 执行+查询函数
    def execute(self,sqlcommand, *args, **kwargs):
        conn = self._get_conn_from_pool()
        res = conn.execute(sqlcommand,*args, **kwargs)
        self.idle_conn.put(conn)
        return res


    # 提交函数
    def commit(self):
        pass


if __name__=="__main__":
    import time,random,pymysql
    mysqlpool=MysqlConnPool('192.168.11.127:32001','vesionbook','root','admin')
    result = mysqlpool.query('select id from capture order by id desc limit 1')
    print(result)
    feature_arr = bytearray([random.randint(1,244) for x in range(0,2068)])
    result = mysqlpool.execute('insert into capture (feature,image_id,device_id,create_time) values(%s,%s,%s,%s)',*(feature_arr,'12312312312', '1000', int(time.time())))
    print(result)



