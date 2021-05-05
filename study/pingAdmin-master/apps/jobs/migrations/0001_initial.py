# Generated by Django 2.1.2 on 2021-04-17 07:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='JobInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, unique=True, verbose_name='Job Name')),
                ('content', models.TextField(blank=True, null=True, verbose_name='Content')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='Comment')),
            ],
            options={
                'verbose_name': 'Job Info',
                'verbose_name_plural': 'Job Info',
                'db_table': 'JobInfo',
            },
        ),
        migrations.CreateModel(
            name='JobType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, unique=True, verbose_name='Job Type Name')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='Comment')),
            ],
            options={
                'verbose_name': 'Job Type',
                'verbose_name_plural': 'Job Type',
                'db_table': 'JobType',
            },
        ),
        migrations.AddField(
            model_name='jobinfo',
            name='types',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='jobs.JobType', verbose_name='Job Type'),
        ),
    ]