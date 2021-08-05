
"""Utility functions used across Myapp"""
import sys,os
import numpy as np
from bs4 import BeautifulSoup
import requests,base64,hashlib
from collections import namedtuple
import datetime
from email.utils import make_msgid, parseaddr
import logging
import time,json
from urllib.error import URLError
import urllib.request
import pysnooper
from myapp.utils.celery import session_scope
import croniter
from dateutil.tz import tzlocal

from myapp.tasks.celery_app import celery_app
from myapp.project import push_message
from myapp import app, db, security_manager
conf = app.config
logging.getLogger("task.task1").setLevel(logging.INFO)


# 配置celery任务
@celery_app.task(name="task.task1", bind=True)
def task1(task):

    print('=====================',datetime.datetime.now(),'=====================')
    # push_message(['xx','xx'],'test message')
    # with session_scope(nullpool=True) as dbsession:
    #     try:
    #         pass
    #     except Exception as e:
    #         print(e)







