# -*- coding: utf-8 -*-
import logging
import os
import platform
import posixpath
import re
import sys
import queue
import threading
from collections import OrderedDict
import multiprocessing
import configparser
import paramiko

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
def ping(host):
    """
    Returns True if host responds to a ping request
    """
    # Ping parameters as function of OS
    ping_str = "n" if platform.system().lower() == "windows" else "c"
    # Ping
    return os.system("ping -" + ping_str + " 1 " + host) == 0


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
                logging.info('Fail to create remote path, server: %s, path: %s expt: {%s}' % (self._host_info.hostname, remote_dir, expt))
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
            logging.info('Fail to find remote file, server: %s, path: %s expt: {%s}' % (self._host_info.hostname, remote_file, expt))
            return False
        # check dir exist on PC
        local_dir = os.path.normpath(local_dir)
        if not os.path.isdir(local_dir):
            try:
                os.makedirs(local_dir)
            except OSError as expt:
                logging.info('Fail to create local dir, server: %s, path: %s expt: {%s}' % (self._host_info.hostname, local_dir, expt))
                return False
        # download file
        try:
            local_file = os.path.join(local_dir, posixpath.basename(remote_file))
            sftp.get(remote_file, local_file)
            return True
        except Exception as expt:
            logging.info('SFTP Download Failed. server: %s, path: %s expt: {%s}' % (self._host_info.hostname, remote_file, expt))
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
            logging.info('Fail to find remote file, server: %s, path: %s expt: {%s}' % (self._host_info.hostname, remote_file, expt))
            return False
        # remove file
        try:
            sftp.remove(remote_file)
            return True
        except Exception as expt:
            logging.info('Fail to remove remote file, server: %s, path: %s expt: {%s}' % (self._host_info.hostname, remote_file, expt))
            return False

def find_file(full_path, rule_file_name=None, rule_content=None, rule_read_len=None, rule_folder_name=None):
    if os.path.isfile(full_path):
        if (not rule_file_name) or re.search(rule_file_name, full_path):
            file_name = os.path.split(full_path)[1]
            if rule_content:
                with open(full_path, 'r') as fd:
                    if rule_read_len:
                        file_data = fd.read(rule_read_len)
                    else:
                        file_data = fd.read()
                    if not re.search(rule_content, file_data):
                        return
            yield full_path
    if os.path.isdir(full_path):
        if (not rule_folder_name) or re.search(rule_folder_name, full_path):
            for path in os.listdir(full_path):
                for file_name in find_file(os.path.join(full_path, path), rule_file_name, rule_content,
                                                rule_read_len,
                                                rule_folder_name):
                    yield file_name


def ReadBlanceIni(inifile):
    try:
        config = configparser.ConfigParser()
        config.read(inifile)
        section_list = config.sections()
        ip_port_dict = {}
        for section in section_list:
            option_list = config.options(section)
            if "wds11_ip" in option_list:
                wds11_ip, wds11_port = config.get(section, "wds11_ip"), config.get(section, "wds11_port")
                if wds11_ip in list(ip_port_dict.keys()):
                    tmp = []
                    for port in ip_port_dict[wds11_ip]:
                        if port not in tmp:
                            tmp.append(port)
                    tmp.append(wds11_port)
                    list(set(tmp))
                    ip_port_dict[wds11_ip] = tmp
                else:
                    ip_port_dict[wds11_ip] = [wds11_port]
            if "wds12_ip" in option_list:
                wds12_ip, wds12_port = config.get(section, "wds12_ip"), config.get(section, "wds12_port")
                if wds12_ip in list(ip_port_dict.keys()):
                    tmp = []
                    for port in ip_port_dict[wds12_ip]:
                        if port not in tmp:
                            tmp.append(port)
                    tmp.append(wds12_port)
                    list(set(tmp))
                    ip_port_dict[wds12_ip] = tmp
                else:
                    ip_port_dict[wds12_ip] = [wds12_port]
            if "wds13_ip" in option_list:
                wds13_ip, wds13_port = config.get(section, "wds13_ip"), config.get(section, "wds13_port")
                if wds13_ip in list(ip_port_dict.keys()):
                    tmp = []
                    for port in ip_port_dict[wds13_ip]:
                        if port not in tmp:
                            tmp.append(port)
                    tmp.append(wds13_port)
                    list(set(tmp))

                    ip_port_dict[wds13_ip] = tmp
                else:
                    ip_port_dict[wds13_ip] = [wds13_port]
    except configparser.NoSectionError as e:
        logging.info('Section Error')
        sys.exit(4)
    except configparser.DuplicateSectionError as e:
        logging.info('Duplicate Section Error')
        sys.exit(5)
    except configparser.NoOptionError as e:
        logging.info('Option Error')
        sys.exit(6)
    else:
        ip_port_dict_result=OrderedDict()
        for _ip_port_key,_ip_port_value in ip_port_dict.items():
            ip_port_dict_result[_ip_port_key]=sorted(set(_ip_port_value))
        return ip_port_dict_result


def doTask_hostCommand(cmd, **kwargs):  # 具体执行任务
    return_data = OrderedDict()
    return return_data


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
    host_info = OrderedDict()
    host_info = {
        "work_server":
            {
                "host": "10.18.5.149",
                "user": 'a23',
                "passwd": "12345"
            },
        "A_Block_WDS":
            {
                "host": "10.18.5.168",
                "user": 'sysadmin',
                "passwd": "sysadmin"
            },
        "B_Block_WDS":
            {
                "host": "10.18.5.56",
                "user": 'sysadmin',
                "passwd": "sysadmin"
            },
        "D_Block_WDS":
            {
                "host": "10.18.5.169",
                "user": 'sysadmin',
                "passwd": "sysadmin"
            },
        "N11-L11_Block_WDS":
            {
                "host": "10.18.5.118",
                "user": 'sysadmin',
                "passwd": "sysadmin"
            },
        "N21-O11_Block_WDS":
            {
                "host": "10.18.5.157",
                "user": 'sysadmin',
                "passwd": "sysadmin"
            },
        "K_Block_WDS":
            {
                "host": "10.18.5.100",
                "user": 'sysadmin',
                "passwd": "sysadmin"
            },
        "T_Block_WDS":
            {
                "host": "10.18.9.125",
                "user": 'sysadmin',
                "passwd": "sysadmin"
            },
        "S_Block_WDS":
            {
                "host": "10.18.9.145",
                "user": 'sysadmin',
                "passwd": "sysadmin"
            }
    }
    ssh_plug = SSHTunnel()
    # Start the connection
    for key, value in host_info.items():
        flag = ssh_plug.connect(hostname=value["host"], username=value["user"], password=value["passwd"],port="22")
        if "N11-L11_Block_WDS" in key:
            balance_ini_folder = "/home/wyc/chrome_data/0GE_modrin/ZTE/toolkit/"
            ssh_plug.get_file("/home/sysadmin/server_config/balance/0GE.ini", balance_ini_folder)
            result = ReadBlanceIni(balance_ini_folder+"0GE.ini")
            # result = HOSTConn.run_cmd("df -h")
            print(key, result)
    # serverMapping=OrderedDict()
    # with open("/home/wyc/chrome_data/SMTShopfloor_update/servermapping.csv") as f:
    #     s = f.readlines()
    #     for line in s:
    #         serverMapping[line.split(",")[1].strip()]=line.split(",")[0].strip()
    # for file in find_file("/home/wyc/chrome_data/SMTShopfloor_update/balance",
    #                       rule_file_name="\/root/0GE.ini$"):
    #     result = ReadBlanceIni(file)
    #     print(file)
    #     for key,value in result.items():
    #         print(serverMapping[key],key,value)
