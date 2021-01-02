# -*- coding: utf-8 -*-
import threading

import queue
import threading

from collections import OrderedDict
import multiprocessing

import mutablerecords as mutablerecords
import paramiko


class SSHParamiko(object):
    err = "argument passwd or rsafile can not be None"

    def __init__(self, host,user, passwd=None,port="22", rsafile=None):
        self.h = host
        self.p = port
        self.u = user
        self.w = passwd
        self.rsa = rsafile

    def _connect(self):
        if self.w:
            return self.pwd_connect()
        elif self.rsa:
            return self.rsa_connect()
        else:
            raise ConnectionError(self.err)

    def _transfer(self):
        if self.w:
            return self.pwd_transfer()
        elif self.rsa:
            return self.rsa_transfer()
        else:
            raise ConnectionError(self.err)

    def pwd_connect(self):
        conn = paramiko.SSHClient()
        conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        conn.connect(self.h, self.p, self.u, self.w)
        return conn

    def rsa_connect(self):
        pkey = paramiko.RSAKey.from_private_key_file(self.rsa)
        conn = paramiko.SSHClient()
        conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        conn.connect(hostname=self.h, port=self.p, username=self.u, pkey=pkey)
        return conn

    def pwd_transfer(self):
        transport = paramiko.Transport(self.h, self.p)
        transport.connect(username=self.u, password=self.w)
        sftp = paramiko.SFTPClient.from_transport(transport)
        return sftp, transport

    def rsa_transfer(self):
        pkey = paramiko.RSAKey.from_private_key_file(self.rsa)
        transport = paramiko.Transport(self.h, self.p)
        transport.connect(username=self.u, pkey=pkey)
        sftp = paramiko.SFTPClient.from_transport(transport)
        return sftp, transport

    def run_cmd(self, cmd):
        conn = self._connect()
        stdin, stdout, stderr = conn.exec_command(cmd)
        code = stdout.channel.recv_exit_status()
        stdout, stderr = stdout.read(), stderr.read()
        conn.close()
        if not stderr:
            return code, stdout.decode()
        else:
            return code, stderr.decode()

    def get_file(self, remote, local):
        sftp, conn = self._transfer()
        sftp.get(remote, local)
        conn.close()

    def put_file(self, local, remote):
        sftp, conn = self._transfer()
        sftp.put(local, remote)
        conn.close()

class Autistic(object):
    def __init__(self, **kwargs):
        self._kwargs = kwargs
        self._connected = True
        self._cond = threading.Condition()
        self._results = dict()
        self._requests = multiprocessing.Queue()
        self._responses = multiprocessing.Queue()
        self._thread = threading.Thread(target=self._host_thread)
        self._process = multiprocessing.Process(target=_autistic_process,
                                                args=(self._requests, self._responses, self._kwargs))
        self._thread.daemon = True
        self._thread.start()
        self._process.daemon = True
        self._process.start()

    def __getattr__(self, name):
        if name in self._kwargs:
            return self._kwargs[name]
        def _send(*args):
            tid = threading.current_thread().ident
            self._send_request([tid, name, args])
            ret = self._get_result(tid)
            if isinstance(ret, Exception):
                raise ret
            return ret

        return _send

    def close(self):
        print("close process func call")
        if self._process.is_alive():
            self._requests.put(None)
            self._process.join()
        self._connected = False
        if self._thread.is_alive():
            self._thread.join()
        self._requests.close()
        self._responses.close()

    def _send_request(self, request):
        while self._process.is_alive():
            try:
                self._requests.put(request, timeout=0.1)
                return
            except queue.Full as e:
                continue
        raise Exception('Device disconnected')

    def _get_result(self, id):
        while self._connected:
            with self._cond:
                if id in self._results:
                    return self._results.pop(id)
                self._cond.wait(timeout=0.1)
            if not self._connected:
                break
        raise Exception('Device disconnected')

    def _host_thread(self):

        while self._connected:
            try:
                response = self._responses.get(timeout=0.1)
            except queue.Empty as e:
                continue
            except Exception as ne:
                continue
            with self._cond:
                self._results[response[0]] = response[1]
                self._cond.notify_all()


def _autistic_process(requests, responses, kwargs):
    while True:
        request = requests.get()
        if request is None:
            break
        try:
            multiprocessing.get_logger().warning('request : {}'.format(request))
            multiprocessing.get_logger().warning('kwargs : {}'.format(kwargs))
            result = eval(request[1])(*request[2], **kwargs)
            multiprocessing.get_logger().warning('result : {}'.format(result))
        except Exception as e:
            result = e
        responses.put([request[0], result])


def doTask_hostCommand(func,cmd, **kwargs):  # 具体执行任务
    HOSTConn =  SSHParamiko(host="10.18.5.149",user='a23',passwd="12345")

    return_data = OrderedDict()
    Autistic(**kwargs)
    return return_data

if __name__ == '__main__':
    host_info={
        "host" : "10.18.5.149", "user" : 'a23', "passwd" : "12345"
    }
    host_conn = doTask_hostCommand("run_cmd","df -h",host_info)











