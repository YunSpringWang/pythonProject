from django.db import models
from django.utils.translation import ugettext_lazy as _
from apps.utils.models import BaseModel

# Create your models here.

class AssetGroup(models.Model):
    name = models.CharField(max_length=64, verbose_name=_('Asset Group Name'), unique=True)
    comment = models.TextField(verbose_name=_('Comment'), blank=True, null=True)

    class Meta:
        db_table = 'AssetGroup'
        verbose_name = _('Asset Group')
        verbose_name_plural = _('Asset Group')

    def __str__(self):
        return self.name


class AssetInfo(models.Model):
    asset_type_choice = (
        ('server', '服务器'),
        ('WDSserver', 'WDS服务器'),
        ('networkdevice', '网络设备'),
        ('storagedevice', '存储设备'),
        ('securitydevice', '安全设备'),
        # ('software', '软件资产'), # 软件资产单独一个表
    )
    sub_asset_type_choice = (
        (0, 'WDS_server'),
        (1, 'SF_server'),
        (2, 'Dome_server'),
    )

    asset_status = (
        (0, '在线'),
        (1, '下线'),
        (2, '未知'),
        (3, '故障'),
        (4, '备用'),
        )

    # basic info
    hostname = models.CharField(max_length=64, verbose_name=_('Hostname'), unique=True)
    asset_type = models.CharField(choices=asset_type_choice, max_length=64, default='server', verbose_name="资产类型")
    asset_sub_type = models.SmallIntegerField(choices=sub_asset_type_choice, max_length=64, default=2, verbose_name="资产子类型")
    outer_ip = models.GenericIPAddressField(max_length=32, verbose_name=_('Outer IP'), null=True, blank=True)
    inner_ip = models.GenericIPAddressField(max_length=32, verbose_name=_('Inner IP'), null=True, blank=True)
    port = models.IntegerField(default=22, verbose_name=_('Port'), null=True, blank=True)
    status = models.SmallIntegerField(choices=asset_status, default=0, verbose_name='设备状态')
    username = models.CharField(max_length=64, verbose_name=_('Username'), null=True, blank=True)
    password = models.CharField(max_length=128, verbose_name=_('Auth Password'), default='', blank=True)
    groups = models.ForeignKey(to='AssetGroup', verbose_name=_('Asset Group'), on_delete=models.SET_NULL, blank=True, null=True)
    # system info from salt
    os = models.CharField(max_length=64, verbose_name=_('OS'), null=True, blank=True)
    os_release = models.CharField(max_length=32, verbose_name=_('OS Release'), null=True, blank=True)
    cpu_model = models.CharField(max_length=64, verbose_name=_('CPU Model'), null=True, blank=True)
    cpu_count = models.IntegerField(null=True, verbose_name=_('CPU Count'))
    mem_total = models.CharField(max_length=64, verbose_name=_('Memory Total'), null=True, blank=True)
    sn = models.CharField(max_length=64, verbose_name=_('Serial Number'), null=True, blank=True)

    class Meta:
        db_table = 'AssetInfo'
        verbose_name = _('Asset Info')
        verbose_name_plural = _('Asset Info')

    def __str__(self):
            return '%s--%s--%s' % (self.hostname, self.get_sub_asset_type_display(), self.asset_type_choice())


