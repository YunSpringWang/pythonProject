from datetime import datetime

import pymysql
from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse
from django.contrib import auth
from django.views import View
######################################
# 自建模块
######################################
from .utils.validCode import get_valid_code_img  # 导入自己创建的工具文件utils
from .utils.JsonFormatTool import *  # 导入自己创建的工具文件utils
from .models import *

######################################
# 第三方模块
######################################
from pure_pagination import PageNotAnInteger, Paginator, EmptyPage


def login(request):
    if request.method == 'GET':
        return render(request, 'login.html')
    else:
        # Json 返回登陆结果
        response = {'user': None, 'msg': None}
        # 提交的登陆post
        user = request.POST.get('user')
        pwd = request.POST.get('pwd')
        valid_code = request.POST.get('valid_code')  # 图片验证码

        # 获取到session中的验证码值
        valid_code_str = request.session.get('valid_code_str')

        if valid_code.upper() == valid_code_str.upper():  # 不区分大小写
            # 进行账号认证
            user = auth.authenticate(username=user, password=pwd)
            if user:  # 有这个用户
                auth.login(request, user)  # request.user == 当前登陆对象
                response['user'] = user.username
            else:
                response['msg'] = '用户名或密码错误！'

        else:
            response['msg'] = '验证码错误'

        return JsonResponse(response)


def get_validCode_img(request):
    """
    给予PIL模块动态生产验证码
    :param request:
    :return:
    """
    data = get_valid_code_img(request)
    return HttpResponse(data)


def homepage(request):
    return render(request, 'index.html')


class Struct(dict):
    """
    - 为字典加上点语法. 例如:
    >>> o = Struct({'a':1})
    >>> o.a
    >>> 1
    >>> o.b
    >>> None
    """

    def __init__(self, dictobj={}):
        self.update(dictobj)

    def __getattr__(self, name):
        # Pickle is trying to get state from your object, and dict doesn't implement it.
        # Your __getattr__ is being called with "__getstate__" to find that magic method,
        # and returning None instead of raising AttributeError as it should.
        if name.startswith('__'):
            raise AttributeError
        return self.get(name)

    def __setattr__(self, name, val):
        self[name] = val

    def __hash__(self):
        return id(self)


def paginator(data_list, per_page, page_no):
    """
       功能说明      封装Django自带的分页函数
       接收三个值：需要分页的对象，每页多少条数据，需要返回的页码
       返回三个值：分页后的对象，需要返回的页码，分页信息
       """
    data = Struct()
    from django.core.paginator import Paginator
    pages = Paginator(data_list, per_page)

    # 防止超出页数
    if not page_no > 0:
        page_no = 1
    if page_no > pages.num_pages:
        page_no = pages.num_pages

    p = pages.page(page_no)
    data.count = pages.count
    data.page_num = pages.num_pages
    data.per_page = per_page
    data.current = page_no
    data.start_index = p.start_index() - 1

    return p.object_list, page_no, data


def chromebookhome(request):
    if request.method == "GET":
        pageSize = request.GET.get('pageSize')
        pageNumber = request.GET.get('pageNumber')
        searchText = request.GET.get('searchText')
        sortName = request.GET.get('sortName')
        sortOrder = request.GET.get('sortOrder')

        test_data = {
            "data_id": 1,
            "ipaddr_name": "localhost",
            "ipaddr_public": "127.0.0.1",
            "ipaddr_inner": "10.17.80.58",
            "quanta_model": "0GJ",
            "google_model": "Drawlat",
            "HP_model": "Hitchcock",
            "ipType": 2,
            "ip_Port": "7161",
            "ipstatus": 1,
            "engine_manager": "spring wang"
        }
        test_data2 = {
            "data_id": 2,
            "ipaddr_name": "localhost",
            "ipaddr_public": "127.0.0.1",
            "ipaddr_inner": "10.17.80.58",
            "quanta_model": "0GJ",
            "google_model": "Drawlat",
            "HP_model": "Hitchcock",
            "ipType": 2,
            "ip_Port": "7161",
            "ipstatus": 1,
            "engine_manager": "spring wang"
        }
        rows = []
        rows.append(test_data)
        rows.append(test_data2)
        data = {"errcode": 0,
                "errmsg": "ok",
                "count": 3,
                "data": rows}
        return_dict = {"ret": True, "errMsg": "", "rows": rows, "total": "1"}

        return render(request, 'chromebook/chrome_server_list.html', {"ret": json.dumps(return_dict)})


######################################
# 主机列表
######################################
def HostListView(request):
    if request.method == "GET":
        # 获取主机记录
        host_records = HostInfo.objects.filter(host_port_status=1).order_by('-update_time')
        print(host_records)
        # 筛选条件
        # 记录数量
        record_nums = host_records.count()

        # 判断页码
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1

        # 对取到的数据进行分页，记得定义每页的数量
        p = Paginator(host_records, 5, request=request)

        # 分页处理后的 QuerySet
        host_records = p.page(page)
        context={
            'host_records': host_records,
        }
        return render(request, 'chromebook/host_list.html', context=context)


######################################
# 添加主机
######################################
class AddHostInfoView(View):
    def post(self, request):
        host = HostInfo()
        host.in_ip = request.POST.get('in_ip')
        host.out_ip = request.POST.get('out_ip', '')
        host.system_id = int(request.POST.get('system'))
        host.hostname = request.POST.get('hostname')
        host.cpu = request.POST.get('cpu')
        host.disk = int(request.POST.get('disk'))
        host.memory = int(request.POST.get('memory'))
        host.network = int(request.POST.get('network'))
        host.ssh_port = int(request.POST.get('ssh_port'))
        host.root_ssh = request.POST.get('root_ssh')
        host.op_env_id = int(request.POST.get('op_env'))
        host.use_id = int(request.POST.get('use'))
        host.project_id = int(request.POST.get('project'))
        host.idc_id = int(request.POST.get('idc'))
        host.admin_user = request.POST.get('admin_user')
        host.admin_pass = request.POST.get('admin_pass')
        host.normal_user = request.POST.get('normal_user', '')
        host.normal_pass = request.POST.get('normal_pass', '')
        host.op_user_id = int(request.POST.get('op_user'))
        host.update_user = request.user
        host.desc = request.POST.get('desc', '')
        host.save()
        return HttpResponse('{"status":"success", "msg":"主机信息添加成功！"}', content_type='application/json')

######################################
# 主机列表
######################################
def CheckServerDetailsView(request):
    if request.method == "GET":
        # 获取主机记录
        host_records = HostInfo.objects.filter(host_port_status=1).order_by('-update_time')
        print(host_records)
        # 筛选条件
        # 记录数量
        record_nums = host_records.count()

        # 判断页码
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1

        # 对取到的数据进行分页，记得定义每页的数量
        p = Paginator(host_records, 5, request=request)

        # 分页处理后的 QuerySet
        host_records = p.page(page)
        context={
            'host_records': host_records,
        }
        return render(request, 'chromebook/query_check_server_details.html', context=context)
