#!/usr/bin/env python
from datetime import datetime
import logging
from subprocess import Popen
from sys import stdout

import click
from colorama import Fore, Style
from flask import g
from flask_appbuilder import Model

from myapp import app, appbuilder, db, security_manager
from myapp.utils import core as utils

conf = app.config

def create_app(script_info=None):
    return app

@app.shell_context_processor
def make_shell_context():
    return dict(app=app, db=db)

import pysnooper

# https://dormousehole.readthedocs.io/en/latest/cli.html
@app.cli.command('init')
def init():
    """Inits the Myapp application"""
    appbuilder.add_permissions(update_perms=True)   # update_perms为true才会检测新权限
    security_manager.sync_role_definitions()






