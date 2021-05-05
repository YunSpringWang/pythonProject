# -*- coding: utf-8 -*-
import logging
import os
import posixpath
import queue
import threading
from collections import OrderedDict
import multiprocessing
import paramiko
import json
import Tools
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


class SSHTunnel:
    def __init__(self):
        self._connected = False
        self.hostname = None
        self.username = None
        self.password = None
        self.port = None

        # set client
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def set_host_info(self, hostname, username, password, port):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port

    def get_host_info(self):
        return [self.hostname, self.username, self.password, self.port]

    def connect(self, hostname=None, username=None, password=None, port=None, timeout=3, retry=3):
        if hostname and username and password and port:
            logging.info('Set host info')
            self.set_host_info(hostname, username, password, port)
        else:
            [hostname, username, password, port] = self.get_host_info(hostname, username, password, port)
        for index in range(0, retry):
            try:
                self.client.connect(hostname=hostname,
                                    port=port,
                                    username=username,
                                    password=password,
                                    allow_agent=False,
                                    look_for_keys=False,
                                    timeout=timeout)
            except:
                self.client.close()
                logging.info('Try to connect server %s %d times' % (self.hostname, index + 1))
                continue

            logging.info('Connected to server %s' % self.hostname)
            self._connected = True
            return True

        if not self._connected:
            logging.info('Fail to connect to server %s' % self.hostname)
            return False

    def disconnect(self):
        try:
            self.client.close()
        except:
            logging.info('Fail to disconnect from server %s' % self.hostname)
            return False
        self._connected = False
        logging.info('Disconnected from server %s' % self.hostname)
        return True

    def run_cmd(self, command):
        if not self._connected:
            logging.info('Lost connection on server: %s', self._host_info)
            return False, '', ''
        try:
            _, stdout, stderr = self.client.exec_command(command, get_pty=True)
            return True, stdout.read(), stderr.read()
        except Exception as expt:
            logging.info('Failed to run command: %s, except: %s' % (command, expt))
            self.disconnect()
            return False, '', ''

    def put_file(self, local_file, remote_dir):
        # check connection
        if not self._connected:
            logging.info('Lost connection on server: %s' % self._host_info)
            return False
        # open sftp
        try:
            sftp = self.client.open_sftp()
        except Exception as expt:
            logging.info('Fail to create SFTP, server: %s, expt: {%s}' % (self._host_info.hostname, expt))
            return False
        # check file exist on PC
        local_file = os.path.normpath(local_file)
        if not os.path.exists(local_file) or os.path.isdir(local_file):
            logging.info('Fail to find path %s' % local_file)
            return False
        # check dir exist on DUT
        remote_dir = posixpath.normpath(remote_dir)
        if posixpath.isdir(remote_dir):
            try:
                sftp.mkdir(remote_dir)
            except Exception as expt:
                logging.info('Fail to create remote path, server: %s, path: %s expt: {%s}' % (
                self._host_info.hostname, remote_dir, expt))
                return False
        try:
            sftp.chdir(remote_dir)
        except:
            logging.info('Fail to access remote path')
            return False
        # Upload file
        try:
            remote_file = posixpath.join(remote_dir, os.path.basename(local_file))
            sftp.put(local_file, remote_file)
            return True
        except Exception as expt:
            logging.info('SFTP Uploading Failed, server: %s, expt: {%s}' % (self._host_info.hostname, expt))
            return False

    def get_file(self, remote_file, local_dir):
        # check connection
        if not self._connected:
            logging.info('Lost connection on server: %s', self._host_info)
            return False
        # open sftp
        try:
            sftp = self.client.open_sftp()
        except Exception as expt:
            logging.info('Fail to create SFTP connection, server: %s, expt: {%s}' % (self._host_info.hostname, expt))
            return False
        # check file exist on DUT
        remote_file = posixpath.normpath(remote_file)
        try:
            sftp.stat(remote_file)
        except Exception as expt:
            logging.info('Fail to find remote file, server: %s, path: %s expt: {%s}' % (
            self._host_info.hostname, remote_file, expt))
            return False
        # check dir exist on PC
        local_dir = os.path.normpath(local_dir)
        if not os.path.isdir(local_dir):
            try:
                os.makedirs(local_dir)
            except OSError as expt:
                logging.info('Fail to create local dir, server: %s, path: %s expt: {%s}' % (
                self._host_info.hostname, local_dir, expt))
                return False
        # download file
        try:
            local_file = os.path.join(local_dir, posixpath.basename(remote_file))
            sftp.get(remote_file, local_file)
            return True
        except Exception as expt:
            logging.info(
                'SFTP Download Failed. server: %s, path: %s expt: {%s}' % (self._host_info.hostname, remote_file, expt))
            return False

    def remove(self, remote_file):
        # open sftp
        try:
            sftp = self.client.open_sftp()
        except Exception as expt:
            logging.info('Fail to create SFTP connection, server: %s, expt: {%s}' % (self._host_info.hostname, expt))
            return False
        # check file exist
        remote_file = posixpath.normpath(remote_file)
        try:
            sftp.stat(remote_file)
        except Exception as expt:
            logging.info('Fail to find remote file, server: %s, path: %s expt: {%s}' % (
            self._host_info.hostname, remote_file, expt))
            return False
        # remove file
        try:
            sftp.remove(remote_file)
            return True
        except Exception as expt:
            logging.info('Fail to remove remote file, server: %s, path: %s expt: {%s}' % (
            self._host_info.hostname, remote_file, expt))
            return False


def doTask_hostCommand(cmd, **kwargs):  # 具体执行任务
    return_data = OrderedDict()
    return return_data


class MappingServerListVersion():
    def read_active_json(self, mode=None):
        for file in Tools.find_file("/cros_docker/umpire/", rule_file_name="\/active_umpire.json$"):
            file_folder = os.path.dirname(file)
            with open(file, 'r') as active_umpire_json_file:
                active_umpire_json = json.load(active_umpire_json_file)
                for bundles in active_umpire_json["bundles"]:
                    if bundles['id'] == active_umpire_json["active_bundle_id"]:
                        payloads_file_path = os.path.join(file_folder, "resources", bundles["payloads"])
                        self.read_payloads_json(payloads_file_path)

    def read_payloads_json(self, payloads_file_path):
        try:
            with open(payloads_file_path, 'r') as payloads_json:
                payloads_dict = json.load(payloads_json)
                release_image_version = payloads_dict["release_image"]["version"]
                test_image_version = payloads_dict["test_image"]["version"]
                firmware_file = payloads_dict["firmware"]["file"]
                toolkit_file = payloads_dict["toolkit"]["file"]
                hwid_version = payloads_dict["hwid"]["version"]
                print(release_image_version, test_image_version, firmware_file, toolkit_file, hwid_version)
        except Exception as e:
            print("{} NotFound in {}".format(e,payloads_file_path))
            pass

    def read_balance_ini(self, mode):
        serverMapping = OrderedDict()
        with open("/home/wyc/chrome_data/SMTShopfloor_update/servermapping.csv") as f:
            s = f.readlines()
            for line in s:
                serverMapping[line.split(",")[1].strip()] = line.split(",")[0].strip()
        for file in Tools.find_file("/home/wyc/chrome_data/SMTShopfloor_update/balance",
                              rule_file_name="\/root/{}.ini$".format(mode)):
            result = Tools.ReadBlanceIni(file)
            print(file)
            for key, value in result.items():
                print(serverMapping[key], key, value)


if __name__ == '__main__':
    """
    # 参数
    multiprocessing.Process(group=None, target=None, name=None, args=(), kwargs={})
    - group：分组，实际上很少使用
    - target：表示调用对象，你可以传入方法的名字
    - name：别名，相当于给这个进程取一个名字
    - args：表示被调用对象的位置参数元组，比如target是函数a，他有两个参数m，n，那么args就传入(m, n)即可
    - kwargs：表示调用对象的字典
    """
    mapping_version = MappingServerListVersion()
    # mapping_version.read_balance_ini("0GCD")
    mapping_version.read_active_json("0GE")
