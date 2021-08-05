import pymysql
import pymysql.cursors
import logging
import time


class PyMysql:
    def __init__(self):
        self.conn = None
        self.cursor = None
    # 链接mysql数据库
    def connect(self, host, user, passwd, db, port=3306, charset="utf8"):
        try:
            self.conn = pymysql.connect(host=host, user=user, passwd=passwd, db=db, port=port, charset=charset,
                                        cursorclass=pymysql.cursors.DictCursor, )
            self.cursor = self.conn.cursor()
            # logging.info('connect mysql success')
        except Exception as e:
            logging.error('connect mysql database %s error! %s' % (db, e))
            return False
        return True
    # 切换游标
    def switch_cursor(self, curclass):
        if not isinstance(curclass, (pymysql.cursors.Cursor, pymysql.cursors.DictCursor,
                                     pymysql.cursors.SSCursor, pymysql.cursors.SSDictCursor)):
            logging.debug('invalid cursor class： %s' % (type(curclass), ))
            return False
        self.cursor = self.conn.cursor(cursorclass=curclass)
        return True

    # 指定sql命令查询
    def query(self, sqlcommand, args=None):
        try:
            self.cursor = self.conn.cursor()
            self.cursor.execute(sqlcommand, args)
            result = self.cursor.fetchall()
            self.conn.commit()
        except Exception as e:
            logging.error("mysql query error: %s\n mysql:%s args: %s" %(e, sqlcommand, args))
            return False
        return result

    # 指定sql命令执行
    def execute(self, sqlcommand, args=None):
        try:
            self.cursor = self.conn.cursor()
            if isinstance(args, (list, tuple)) and len(args) > 0 and \
                    isinstance(args[0], (list, tuple)):
                line = self.cursor.executemany(sqlcommand, args)
            else:
                line = self.cursor.execute(sqlcommand, args)
        except Exception as e:
            # traceback.print_exc()
            logging.error("mysql execute error: %s"% e)
            return False
        return line, self.cursor

    # 提交
    def commit(self):
        self.conn.commit()

    # 回滚
    def rollback(self):
        self.conn.rollback()

    # 关闭链接
    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        # logging.info('close mysql success')

    # 插入数据
    def insert_data(self, table_name, data_dict):
        data_values = "(" + "%s," * (len(data_dict)) + ")"
        data_values = data_values.replace(',)', ')')
        db_field = data_dict.keys()
        data_tuple = tuple(data_dict.values())
        db_field = str(tuple(db_field)).replace("'", '')
        sql = """ insert into %s %s values %s """ % (table_name, db_field, data_values)
        params = data_tuple

        self.execute(sql, params)
        self.commit()
        #self.close()

    # 创建或修改数据
    def insert_update_data(self,table_name, data_dict,major_key):
        data_values = "(" + "%s," * (len(data_dict)) + ")"
        data_values = data_values.replace(',)', ')')
        db_field = data_dict.keys()
        data_tuple = tuple(data_dict.values())
        db_field = str(tuple(db_field)).replace("'", '')
        sql = 'select '+major_key+' from '+table_name+' where '+major_key+'=%s'
        major_value = data_dict[major_key]
        exist_data = () # self.query(sql,*(major_value,))
        print(sql,major_value,exist_data)

        if not exist_data:
            sql = "insert into %s %s values %s " % (table_name, db_field, data_values)
            params = data_tuple
            # print(sql,params)
            self.execute(sql, params)
            self.commit()
        else:
            sql = "update %s set " % table_name
            params=[]
            for key in data_dict:
                if key!=major_key:
                    if type(data_dict[key])==int:
                        sql+=key+"="+str(data_dict[key])+","
                    elif type(data_dict[key])==str:
                        sql += key + "='" + data_dict[key] + "',"
                    elif type(data_dict[key])==bytes:
                        sql += key + "=%s,"
                        params.append(data_dict[key])
            sql=sql[0:-1]
            sql+=" where "+major_key+"=%s"
            params.append(data_dict[major_key])
            # print(sql,params)
            self.execute(sql, params)
            self.commit()


# docker run -p 3306:3306 --name mysql_docker -v $PWD/conf:/etc/mysql/conf.d -v $PWD/logs:/logs -v $PWD/data:/var/lib/mysql -e MYSQL_ROOT_PASSWORD=123456 -d mysql:5.6   运行
#
# mysql -u root -p
# CREATE DATABASE IF NOT EXISTS $PROJECT default charset utf8 COLLATE utf8_general_ci;

def test():
    py_sql = PyMysql()
    py_sql.connect('127.0.0.1', 'root', '123456', 'note', 3306)
    sql = 'drop table if exists user'
    py_sql.cursor.execute(sql)
    py_sql.conn.commit()

    sql = 'drop table if exists product'
    py_sql.cursor.execute(sql)
    py_sql.conn.commit()

    sql = 'drop table if exists user_product'
    py_sql.cursor.execute(sql)
    py_sql.conn.commit()

    create_table = 'create table user(id INTEGER PRIMARY KEY AUTO_INCREMENT ,username varchar(64) not null,password varchar(64) not null, phone varchar(64));'
    py_sql.cursor.execute(create_table)
    py_sql.conn.commit()

    create_table = 'create table product(id INTEGER PRIMARY KEY AUTO_INCREMENT ,type varchar(64) not null,time varchar(64) not null, userid INTEGER,' \
                   'field varchar(64) not null,title varchar(200),content varchar(500),answer varchar(200));'
    py_sql.cursor.execute(create_table)
    py_sql.conn.commit()

    create_table = 'create table user_product(id INTEGER PRIMARY KEY AUTO_INCREMENT ,userid INTEGER not null,productid INTEGER not null, type varchar(64) not null);'
    py_sql.cursor.execute(create_table)
    py_sql.conn.commit()


if __name__ == "__main__":
    py_sql = PyMysql()
    py_sql.connect('47.107.26.202', 'root', 'admin', 'vesionbook', 3306)
    for i in range(30,60):
        timestamp = int(time.mktime(time.strptime('2019-02-26 19:%d:00'%i,'%Y-%m-%d %H:%M:%S')))
        sql='select count(*) from capture where create_time>%s and create_time<%s'%(timestamp,timestamp+60)
        result = py_sql.query(sql)
        print(i+1,result)











    # sql = 'truncate table t_face_1'   # 清空数据表
    # py_sql.execute(sql)
    # py_sql.conn.commit()
    # print('delete t_face_1')
    # sql = 'truncate table t_face_2'  # 清空数据表
    # py_sql.execute(sql)
    # py_sql.conn.commit()
    # print('delete t_face_2')
    # sql = 'truncate table t_face_3'  # 清空数据表
    # py_sql.execute(sql)
    # py_sql.conn.commit()
    # print('delete t_face_3')
    # sql = 'truncate table t_image_1'  # 清空数据表
    # py_sql.execute(sql)
    # py_sql.conn.commit()
    # print('delete t_image_1')
    # sql = 'truncate table t_image_2'  # 清空数据表
    # py_sql.execute(sql)
    # py_sql.conn.commit()
    # print('delete t_image_2')
    # sql = 'truncate table t_image_3'  # 清空数据表
    # py_sql.execute(sql)
    # py_sql.conn.commit()
    # print('delete t_image_3')
    # py_sql.close()





