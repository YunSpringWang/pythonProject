# -*- coding: utf-8 -*-
import paramiko
import os
import time
import re
import sys

login_config = {
    "hostip": "",  # 服务器的ip（需要填写）
    "hostport": 22,  # 端口号
    "username": "lishouxian",  # 登陆的用户名
    "userpwd": "",  # 登陆密码（需要填写）
    "rootusr": "root",  # root 用户
    "rootpwd": "root",  # root 密码
    # 私钥，将配置好的id_rsa文件放在项目目录下
    "keypath": os.path.join(os.path.dirname(os.path.abspath(__file__)), "id_rsa"),
}


# 通过密钥登陆服务器
def login_server_by_rsa():
    try:
        server_ssh = paramiko.SSHClient()
        server_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        pkey = paramiko.RSAKey.from_private_key_file(login_config["keypath"])
        server_ssh.connect(hostname=login_config["hostip"],
                           port=login_config["hostport"],
                           username=login_config["username"],
                           pkey=pkey)
        return server_ssh
    except Exception as e:
        print(e)


# 通过密码登陆服务器
def login_server_by_pwd():
    try:
        server_ssh = paramiko.SSHClient()
        server_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        server_ssh.connect(hostname=login_config["hostip"],
                           port=login_config["hostport"],
                           username=login_config["username"],
                           password=login_config["userpwd"])
        return server_ssh
    except Exception as e:
        print(e)
# 获得root权限
def authenticating_channel(login_ssh):
    channel = login_ssh.invoke_shell()
    try:
        print('............Authenticating............')
        channel.send("su %s\n" % login_config["rootusr"])
        buff = ''
        while not buff.endswith('Password: '):
            resp = channel.recv(10000)
            buff += resp
        print(buff)
        channel.send("%s\n" % login_config["rootpwd"])
        buff = ''
        while not buff.endswith('# '):
            resp = channel.recv(10000)
            buff += resp
        print(buff)
    except Exception as e:
        print(e)
        channel.close()
        login_ssh.close()
    return channel

# 获取服务器时间
def get_server_time():
    ssh = login_server_by_pwd()
    stdin, stdout, stderr = ssh.exec_command('date +%Y-%m-%d\ %H:%M:%S')
    servertime = stdout.read()
    ssh.close()
    return servertime

