# -*- coding: utf-8 -*-
import collections
import logging
import subprocess
import json
import configparser

import paramiko
import os
import time
import re
import sys
password='wyc123'
def execute_cmd(cmd,password):
    '''执行shell命令'''
    p = subprocess.Popen("echo '{}' |sudo -S {}".format(password,cmd), shell=True,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        return p.returncode, stderr
    return p.returncode, stdout

def get_docker_chrome_name():
    cmd = "docker ps"
    return_code,result_stdout = execute_cmd(cmd,password)
    docker_chrome_name =[]
    if return_code ==0:
        result_stdout_list = result_stdout.decode().split("\n")
        for result_line in result_stdout_list[3:]:
            result_line.rfind("/tcp")
            docker_chrome_name.append(result_line[result_line.rfind("/tcp")+len("/tcp"):].strip())
    return docker_chrome_name
def get_docker_item_list_info(docker_chrome_name):
    cmd = "docker inspect -f {} {}".format("{{.LogPath}}", docker_chrome_name)
    docker_chrome = collections.OrderedDict()  # 将普通字典转换为有序字典

    return_code, result_stdout = execute_cmd(cmd, password)
    if return_code == 0:
        result_stdout_list = result_stdout.decode().split("\n")
        with open(result_stdout_list[0]) as logfie:
            data = logfie.readlines()
            for line in data:
                if "process_utils.py" in line:
                    if "cros_payload add .json" in line:
                        reg = "((([0-9]{3}[1-9]|[0-9]{2}[1-9][0-9]{1}|[0-9]{1}[1-9][0-9]{2}|[1-9][0-9]{3})-(((0[13578]|1[02])-(0[1-9]|[12][0-9]|3[01]))|((0[469]|11)-(0[1-9]|[12][0-9]|30))|(02-(0[1-9]|[1][0-9]|2[0-8]))))|((([0-9]{2})(0[48]|[2468][048]|[13579][26])|((0[48]|[2468][048]|[3579][26])00))-02-29))\\s+([0-1]?[0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9])"
                        log_time = re.search(reg, line.split("process_utils.py")[0]).group()
                        result = line.split("cros_payload add .json ")[1].split("/tmp/shared/")
                        upload_filename = result[1].split('\\" in /var/db')[0].split("/")[1]
                        line_data = collections.OrderedDict()  # 将普通字典转换为有序字典
                        line_data["upload_time"]=log_time
                        line_data["upload_filename"]=upload_filename
                        docker_chrome[result[0].strip()] = line_data
    return docker_chrome
def ReadBlanceIni():
    try:
        config_list = ['Setting','WDS11_IP', 'WDS11_PORT', 'WDS12_IP', 'WDS12_PORT', 'TIME']
        config = configparser.ConfigParser()
        config.read("/home/wyc/chrome_data/balance/0GJKL.ini")
        section_list = config.sections()
        use_ip_info = {}
        for section in section_list:
            option_list = config.options(section)
            for option in option_list:
                value = config.get(section, option)
                print(value)
        # IP1 = config.get(section, option)
        # PORT1 = config.getint(section, option1)
        # IP2 = config.get(section, option2)
        # PORT2 = config.getint(section, option3)
        # TIME = config.getint(section, option4)
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
        return None
        # return (IP1,PORT1,IP2,PORT2,TIME)
# docker_chrome_name=get_docker_chrome_name()
# for name in docker_chrome_name:
#     list_info_dict = get_docker_item_list_info(name)
#     for key,item in list_info_dict.items():
#         print(key,item)
ReadBlanceIni()
