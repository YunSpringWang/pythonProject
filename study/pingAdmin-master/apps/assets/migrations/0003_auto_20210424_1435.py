# Generated by Django 2.1.2 on 2021-04-24 06:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0002_auto_20210419_1100'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='server',
            name='asset',
        ),
        migrations.AddField(
            model_name='assetinfo',
            name='asset_sub_type',
            field=models.CharField(choices=[(0, 'WDS_server'), (1, 'SF_server'), (2, 'Dome_server')], default=2, max_length=64, verbose_name='资产子类型'),
        ),
        migrations.DeleteModel(
            name='Server',
        ),
    ]
