import logging
import os
import platform
import re

import configparser
import sys
from collections import OrderedDict


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
def ping(host):
    """
    Returns True if host responds to a ping request
    """
    # Ping parameters as function of OS
    ping_str = "n" if platform.system().lower() == "windows" else "c"
    # Ping
    return os.system("ping -" + ping_str + " 1 " + host) == 0

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
        ip_port_dict_result = OrderedDict()
        for _ip_port_key, _ip_port_value in ip_port_dict.items():
            ip_port_dict_result[_ip_port_key] = sorted(set(_ip_port_value))
        return ip_port_dict_result

