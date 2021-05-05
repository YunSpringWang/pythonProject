from django.db import models

# Create your models here.
from django.utils.translation import ugettext_lazy as _
from apps.utils.models import BaseModel

# Create your models here.

class ModelInfo(BaseModel):
    model_name = models.CharField(max_length=64, verbose_name=_('Model Name'), unique=True)
    release_image_version = models.CharField(max_length=32, blank=True, null=True, verbose_name='出货系统版本')
    test_image_version = models.CharField(max_length=32, blank=True, null=True, verbose_name='测试系统版本')
    toolkit_version = models.CharField(max_length=32, blank=True, null=True, verbose_name='toolkit版本')
    hwid_checksum = models.CharField(max_length=32, blank=True, null=True, verbose_name='toolkit版本')
    firmware_checksum = models.CharField(max_length=32, blank=True, null=True, verbose_name='firmware版本')
    director = models.CharField(max_length=32, blank=True, null=True, verbose_name='负责人')
    model_port=models.CharField(max_length=32, blank=True, null=True, verbose_name='机种端口')
    containerID = models.CharField(max_length=64, blank=True, null=True, verbose_name='容器ID')
    containerName = models.CharField(max_length=255, blank=True, null=True, verbose_name='容器名')
    balance_ini = models.CharField(max_length=255, blank=True, null=True, verbose_name='Balance文件名')

    class Meta:
        db_table = 'ModelInfo'
        verbose_name = _('机种信息')
        verbose_name_plural = _('Model Info')

    def __str__(self):
        return self.name
