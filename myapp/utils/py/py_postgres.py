# -*- coding: utf-8 -*-
# pip install psycopg2-binary
import psycopg2

import logging
import traceback
import time


class PyPostgres:
    def __init__(self):
        self.conn = None
        self.cursor = None
    # 链接mysql数据库
    def connect(self, host, user, passwd, db, port=5432, charset="utf8"):
        try:
            self.conn = psycopg2.connect("host=%s port=%s dbname=%s user=%s password=%s" %(host,port,db,user,passwd))
            self.cursor = self.conn.cursor()
            logging.info('connect postgres success')
        except Exception as e:
            logging.error('connect postgres database %s error! %s' % (db, e))
            return False
        return True

    # 指定sql命令查询
    def query(self, sqlcommand, args=None):
        try:
            self.cursor = self.conn.cursor()
            self.cursor.execute(sqlcommand, args)
            result = self.cursor.fetchall()
        except Exception as e:
            logging.error("postgres query error: %s\n mysql:%s args: %s" %(e, sqlcommand, args))
            return False
        return result

    # 指定sql命令执行
    def execute(self, sqlcommand, args=None):
        try:
            self.cursor = self.conn.cursor()
            if isinstance(args, (list, tuple)) and len(args) > 0 and isinstance(args[0], (list, tuple)):
                line = self.cursor.executemany(sqlcommand, args)
            else:
                line = self.cursor.execute(sqlcommand, args)
            return line
        except Exception as e:
            # traceback.print_exc()
            logging.error("postgres execute error: %s"% e)
            return False


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
        logging.info('close postgres success')

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


# docker run --name postgres1 -e POSTGRES_PASSWORD=admin -p 5432:5432 -d postgres:latest
# su - postgres
# psql
# CREATE DATABASE IF NOT EXISTS testdb default charset utf8 COLLATE utf8_general_ci;



if __name__ == "__main__":
    py_sql = PyPostgres()
    py_sql.connect(host='127.0.0.1', user ='postgres', passwd='admin', db = 'postgres', port = 6432)
    sql = 'drop table if exists public.member'  # 不能使用user ,  因为是postgres关键词
    py_sql.execute(sql)
    py_sql.commit()

    create_table = 'create table public.member(id integer not null primary key ,username varchar(64) not null,password varchar(64) not null, phone varchar(64));'
    py_sql.execute(create_table)
    py_sql.commit()

    insert_data = "insert into public.member(id,username,password,phone) values(1,'luanpeng','123456','112121212');"
    py_sql.execute(insert_data)
    py_sql.commit()

    update_data = "update public.member set username='luanpeng1' where id=1"
    py_sql.execute(update_data)
    py_sql.commit()

    rows = py_sql.query('select * from public.member')
    if rows:
        for row in rows:
            print('id=', row[0], ',username=', row[1], ',password=', row[2], ',phone=', row[3], '\n')

    delete_data = "delete from public.member where id=1"
    py_sql.execute(delete_data)
    py_sql.commit()

    truncate_data = "truncate table public.member"
    py_sql.execute(truncate_data)
    py_sql.commit()


