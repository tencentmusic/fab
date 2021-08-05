import pymysql
import pymysql.cursors
import logging
import traceback
import time
from common.config import *
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class Sqlalchemy:

    def __init__(self,database,user,password,host,port):
        self.db_connection = "mysql+pymysql://%s:%s@%s:%s/%s?charset=utf8" % (user,password,host,port,database)
        self.engine = create_engine(self.db_connection, echo=False, max_overflow=200, pool_size=200)
        self.db_session_maker = sessionmaker(bind=self.engine, autocommit=False, autoflush=False, expire_on_commit=False)




