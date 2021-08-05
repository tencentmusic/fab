#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Based off of code from: www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python
# It's licensed under Public Domain, so we're free to use it.

import traceback
import signal
import copy
import psutil
import sys, os, time, atexit
from signal import SIGTERM
from src.utils.log import Log
from src.utils.process import sync_pid


class RootCheck:
    # The IDs of various accounts.
    # If you're using linux: root=0; it might not in *BSD or others.
    ids = {
        "root": 0
    }

    @staticmethod
    def check(require, check_argv=True):
        if require:
            # If they're not root, tell them to run with root!
            if os.getuid() != RootCheck.ids['root']:
                sys.stdout.write(
                    "This script requires root (id={0}), and you're currently id={1}.\n".format(RootCheck.ids['root'],
                                                                                                os.getuid()))
                sys.stdout.write("Please re-run the script as root (id={0})".format(RootCheck.ids['root']))
                sys.exit(1)
            # If we're checking argv,
            if check_argv and '--requires-root' not in sys.argv:
                sys.stdout.write("To run this script, you must append '--requires-root' to the args.\n")
                sys.stdout.write("This is so that you can't say you didn't know that using root is a bad idea.\n")
                sys.stdout.write("Please re-run the script with '--requires-root'.")
                sys.exit(1)
            # Should we berate them? A warning is enough, really.
            sys.stdout.write("[WARNING!] You've run this script as root, which is bad.\n")

        else:  # down with root, down with root!
            if os.getuid() == RootCheck.ids['root']:
                sys.stdout.write("This script does not require root, but you've given it that anyway.\n")
                sys.stdout.write("It is very poor practice to run a script with more privilege than it needs.\n")
                sys.stdout.write("Please re-run the script without root access")
                sys.exit(1)


class Daemon(object):
    """
	A generic daemon class.

	Usage: subclass the Daemon class and override the run() method
	"""

    def __init__(self, pidfile, daemonize=True, root=False, root_chk_argv=False, stdin="/dev/null", stdout="/dev/null",
                 stderr="/dev/null"):
        """
		Make our daemon instance.
		pidfile: the file we're going to store the process id in. ex: /tmp/matt-daemon.pid
		root:    does this script require root? True if it does, False if it doesn't. Will be enforced.
		root_chk_argv:  does the script require '--requires-root' in sys.argv to run as root? (usage is good)
		stdin:   where the script gets stdin from. "/dev/null", "/dev/stdin", etc.
		stdout:  where the script writes stdout. "/dev/null", "/dev/stdout", etc.
		stderr:  where the script writes stderr. "/dev/null", "/dev/stderr", etc.
		"""
        # Enforce root usage or non-usage.
        # RootCheck.check(root, check_argv=root_chk_argv)
        self.pidfile = pidfile
        self.should_daemonize = daemonize
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr

    def daemonize(self):
        """
		do the UNIX double-fork magic, see Stevens' "Advanced
		Programming in the UNIX Environment" for details (ISBN 0201563177)
		http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
		"""
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError as e:
            sys.stderr.write("fork #1 failed: {0} ({1})\n".format(e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError as e:
            sys.stderr.write("fork #2 failed: {0} ({1})\n".format(e.errno, e.strerror))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(self.stdin, 'a+')
        so = open(self.stdout, 'a+')
        se = open(self.stderr, 'a+')
        if sys.stdin:
            os.dup2(si.fileno(), sys.stdin.fileno())
        if sys.stdout:
            os.dup2(so.fileno(), sys.stdout.fileno())
        if sys.stderr:
            os.dup2(se.fileno(), sys.stderr.fileno())
        # 退出动作
        signal.signal(signal.SIGTERM, self.atexit)  # 捕获kill : SIGTERM信号
        signal.signal(signal.SIGINT,  self.atexit)  # 捕获Ctrl-c: SIGTERM 信号(可以绑定不同的函数)
        signal.signal(signal.SIGTSTP, self.atexit)  # 捕获 Ctrl-z: SIGTSTP信号(可以绑定不同的函数)
        atexit.register(self.delpid)
        #同步pid
        sync_pid()
        signal.signal(SIGTERM, self.stop)  # Gracefully exit on SIGTERM


    def delpid(self):
        if os.path.exists(self.pidfile):
            os.remove(self.pidfile)


    def atexit(self, *args):
        """
        server退出前的清理工作
        :return:
        """
        os._exit(-1)


    def start(self, *args, **kwargs):
        """
		Start the daemon
		"""
        self.make_daemon()
        #执行主逻辑
        self.run(*args, **kwargs)


    def make_daemon(self):
        """

        :return:
        """
        lst_pids = []
        try:
            if os.path.exists(self.pidfile) is True:
                with open(self.pidfile, "r") as pf:
                    lst_pids = [item for item in pf.read().strip().split("|") if item != ""]
        except IOError:
            lst_pids = None
        for item_pid in lst_pids:
            if item_pid.isdigit() is False:
                continue
            process_info = None
            try:
                process_info = psutil.Process(int(item_pid))
            except psutil.NoSuchProcess:
                continue
            if process_info is not None and process_info.is_running() is True:
                message = "server already running in process {0}\n"
                sys.stderr.write(message.format(item_pid))
                sys.exit(1)
        #删除历史存在的文件
        if os.path.exists(self.pidfile):os.remove(self.pidfile)
        if self.should_daemonize:
            # Start the daemon
            self.daemonize()


    def debug(self):
        """

        :return:
        """
        self.stdout = "/dev/stdout"
        self.stdin  = "/dev/stdin"
        self.stderr = "/dev/stderr"
        self.__run_in_front()


    def __run_in_front(self):
        """

        :return:
        """
        # write pidfile
        atexit.register(self.delpid)
        sync_pid()
        try:
            # 退出动作
            self.run()
        except Exception as ex:
            print(traceback.format_exc())
            try:
                self.stop()
            except Exception as ex:
                print(str(ex))
        os._exit(-1)


    def runserver(self):
        """

        :return:
        """
        self.__run_in_front()


    def init(self, *args, **kwargs):
        """
        初始化目录
        :return:
        """
        raise Exception("function init must be overide by child class")


    def manage(self):
        """

        :return:
        """
        self.stdout = "/dev/stdout"
        self.stdin  = "/dev/stdin"
        self.stderr = "/dev/stderr"
        self.start_manage()


    def start_manage(self):
        """

        :return:
        """
        pass


    def stop(self):
        """
		Stop the daemon
		"""
        # Get the pid from the pidfile
        self._stop_server()
        self._on_stop()
        print("stop server successfully")


    def _stop_server(self):
        """

        :return:
        """
        lst_pids = []
        if os.path.exists(self.pidfile) is False:
            message = "pidfile {0} does not exist. Daemon not running?\n"
            sys.stderr.write(message.format(self.pidfile))
            return
        with open(self.pidfile, 'r') as pfile:
            lst_pids = [int(item_pid.strip()) for item_pid in pfile.read().strip().split("|") if item_pid.strip() != ""
                        if item_pid.strip() != ""]
        #kill process
        for item_pid in lst_pids:
            try:
                process_info = psutil.Process(item_pid)
                process_info.kill()
                start_time = time.time()
                #kill超时时间30秒
                running = True
                while time.time() - start_time < 10:
                    try:
                        process_info = psutil.Process(item_pid)
                        if process_info.is_running():
                            running = True
                    except psutil.NoSuchProcess:
                        running = False
                        break
                if running is True:
                    raise Exception("stop server failed, process %s still running after killed" % item_pid)
            except psutil.NoSuchProcess:
                continue
        #删除pid
        if os.path.exists(self.pidfile):os.remove(self.pidfile)


    def _on_stop(self, *args, **kwargs):
        """

        :return:
        """


    def __check_server_running(self):
        """
        检查server是否处于运行中
        :return:
        """
        if os.path.exists(self.pidfile) is False:
            return False
        lst_pids = []
        with open(self.pidfile, 'r') as pfile:
            lst_pids = [int(item_pid.strip()) for item_pid in pfile.read().strip().split("|") if item_pid.strip() != "" if
                        item_pid.isdigit()]
        running = False
        for item_pid in lst_pids:
            try:
                process_info = psutil.Process(item_pid)
                if process_info.is_running() is True:
                    running = True
                    break
            except psutil.NoSuchProcess:
                continue
        return running


    def restart(self):
        """
		Restart the daemon
		"""
        #server运行中，先行终止
        if self.__check_server_running() is True:
            self._stop_server()
        #守护进程
        self.make_daemon()
        #重启时执行
        self._on_restart()


    def _on_restart(self):
        """

        :return:
        """


    def run(self, *args, **kwargs):
        """
		You should override this method when you subclass Daemon. It will be called after the process has been
		daemonized by start() or restart().
		"""
