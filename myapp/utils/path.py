# -*- coding:utf-8 -*-
"""
des: 
create time: 
version: 
"""

import os, errno


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5 (except OSError, exc: for Python <2.5)
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise Exception("create path failed, %s" % path)
