from django.db import models
from datetime import date
# Create your models here.
# ORM模型
# 类 -> 数据库表
# 对象 -> 表中的每一行数据
# 对象.id，对象.value -> 每行中的数据
#这个类是用来生成数据库表的，这个类必须继承models.Model类
######################################
# 主机信息表
######################################
class HostInfo(models.Model):
    host_id =models.CharField(verbose_name='管理员用户', max_length=20)
    inner_ip = models.GenericIPAddressField(verbose_name='内网IP')
    public_ip = models.GenericIPAddressField(verbose_name='公网IP', blank=True, null=True)
    hostname = models.CharField(verbose_name='主机名', max_length=30)
    docker_port = models.IntegerField(verbose_name='远程端口')
    root_ssh = models.BooleanField(verbose_name='是否允许 root 远程', default=True)
    use_type = models.PositiveSmallIntegerField(verbose_name='用途', choices=((1, 'DL服务器'), (2, 'SF服务器'),(3, 'WDS服务器')), default=1)
    quanta_project = models.CharField(verbose_name='广达机种名', max_length=50)
    google_project = models.CharField(verbose_name='google机种名', max_length=50)
    hp_project = models.CharField(verbose_name='HP机种名', max_length=50)
    admin_user = models.CharField(verbose_name='管理员用户', max_length=20)
    admin_pass = models.CharField(verbose_name='管理员密码', max_length=50)
    engine_manager = models.CharField(verbose_name='负责人', max_length=50)
    add_time = models.DateTimeField(verbose_name='添加时间', auto_now_add=True)
    update_user = models.CharField(verbose_name='修改人',max_length=50)
    update_time = models.DateTimeField(verbose_name='修改时间', auto_now=True)
    desc = models.CharField(verbose_name='备注', max_length=200, blank=True, null=True)
    host_port_status = models.PositiveSmallIntegerField(verbose_name='状态', choices=((1, '正常'), (0, '停用')), default=1)

    class Meta:
        verbose_name = '主机信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.host_id