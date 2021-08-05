# -*- coding:utf-8 -*-
"""
des: 
create time: 
version: 
"""

import os
import sys
import signal
import itertools
import threading
from multiprocessing import Process as Proc, Lock, context
from multiprocessing.process import BaseProcess
from src.utils.config import Config
import multiprocessing
from multiprocessing.process import parent_process, _current_process, _process_counter, _children
from multiprocessing import util



class _ParentProcess(BaseProcess):

    def __init__(self, name, pid, sentinel):
        self._identity = ()
        self._name = name
        self._pid = pid
        self._parent_pid = None
        self._popen = None
        self._closed = False
        self._sentinel = sentinel
        self._config = {}

    def is_alive(self):
        from multiprocessing.connection import wait
        return not wait([self._sentinel], timeout=0)

    @property
    def ident(self):
        return self._pid

    def join(self, timeout=None):
        '''
        Wait until parent process terminates
        '''
        from multiprocessing.connection import wait
        wait([self._sentinel], timeout=timeout)

    pid = ident


class ProPidWriteLock(object):

    lock = None
    __instance = None

    def __new__(cls, *args, **kwargs):
        """
        单例模式
        :param args:
        :param kwargs:
        """
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance


    @staticmethod
    def acquire():
        if ProPidWriteLock.lock is None:
            ProPidWriteLock.lock = Lock()
        ProPidWriteLock.lock.acquire()


    @staticmethod
    def release():
        if ProPidWriteLock.lock is None:
            ProPidWriteLock.lock = Lock()
        ProPidWriteLock.lock.release()



def sync_pid():
    """

    :return:
    """
    try:
        ProPidWriteLock.acquire()
        with open(Config.daemon_pid, "a+") as file:
            file.write("|%d" % os.getpid())
    finally:
        ProPidWriteLock.release()


if sys.platform != 'win32':

    class ForkProcess(multiprocessing.process.BaseProcess):
        _start_method = 'fork'
        @staticmethod
        def _Popen(process_obj):
            from multiprocessing.popen_fork import Popen
            return Popen(process_obj)

    class SpawnProcess(multiprocessing.process.BaseProcess):
        _start_method = 'spawn'
        @staticmethod
        def _Popen(process_obj):
            from multiprocessing.popen_spawn_posix import Popen
            return Popen(process_obj)

    class ForkServerProcess(multiprocessing.process.BaseProcess):
        _start_method = 'forkserver'
        @staticmethod
        def _Popen(process_obj):
            from multiprocessing.popen_forkserver import Popen
            return Popen(process_obj)

    class ForkContext(multiprocessing.context.BaseContext):
        _name = 'fork'
        Process = ForkProcess

    class SpawnContext(multiprocessing.context.BaseContext):
        _name = 'spawn'
        Process = SpawnProcess

    class ForkServerContext(multiprocessing.context.BaseContext):
        _name = 'forkserver'
        Process = ForkServerProcess
        def _check_available(self):
            if not multiprocessing.reduction.HAVE_SEND_HANDLE:
                raise ValueError('forkserver start method not available')

    _concrete_contexts = {
        'fork': ForkContext(),
        'spawn': SpawnContext(),
        'forkserver': ForkServerContext(),
    }
    if sys.platform == 'darwin':
        # bpo-33725: running arbitrary code after fork() is no longer reliable
        # on macOS since macOS 10.14 (Mojave). Use spawn by default instead.
        _default_context = multiprocessing.context.DefaultContext(_concrete_contexts['spawn'])
    else:
        _default_context = multiprocessing.context.DefaultContext(_concrete_contexts['fork'])

else:

    class SpawnProcess(multiprocessing.process.BaseProcess):
        _start_method = 'spawn'
        @staticmethod
        def _Popen(process_obj):
            from multiprocessing.popen_spawn_win32 import Popen
            return Popen(process_obj)

    class SpawnContext(multiprocessing.context.BaseContext):
        _name = 'spawn'
        Process = SpawnProcess

    _concrete_contexts = {
        'spawn': SpawnContext(),
    }
    _default_context = multiprocessing.context.DefaultContext(_concrete_contexts['spawn'])


class PathedProcess(multiprocessing.process.BaseProcess):
    _start_method = None
    @staticmethod
    def _Popen(process_obj):
        return _default_context.get_context().Process._Popen(process_obj)


    def _bootstrap(self, parent_sentinel=None):
        global _current_process, _parent_process, _process_counter, _children
        try:
            if self._start_method is not None:
                context._force_start_method(self._start_method)
            _process_counter = itertools.count(1)
            _children = set()
            util._close_stdin()
            old_process = _current_process
            _current_process = self
            _parent_process = _ParentProcess(
                self._parent_name, self._parent_pid, parent_sentinel)
            if threading._HAVE_THREAD_NATIVE_ID:
                threading.main_thread()._set_native_id()
            try:
                util._finalizer_registry.clear()
                util._run_after_forkers()
            finally:
                # delay finalization of the old process object until after
                # _run_after_forkers() is executed
                del old_process
            util.info('child process calling self.run()')
            try:
                sync_pid()
                self.run()
                exitcode = 0
            finally:
                util._exit_function()
        except SystemExit as e:
            if not e.args:
                exitcode = 1
            elif isinstance(e.args[0], int):
                exitcode = e.args[0]
            else:
                sys.stderr.write(str(e.args[0]) + '\n')
                exitcode = 1
        except:
            exitcode = 1
            import traceback
            sys.stderr.write('Process %s:\n' % self.name)
            traceback.print_exc()
        finally:
            threading._shutdown()
            util.info('process exiting with exitcode %d' % exitcode)
            util._flush_std_streams()

        return exitcode



class SpawnProcess(multiprocessing.process.BaseProcess):
    """
    spawn方式启动子进程
    """
    _start_method = None
    @staticmethod
    def _Popen(process_obj):
        return _default_context.get_context("spawn").Process._Popen(process_obj)


# multiprocessing.Process = PathedProcess