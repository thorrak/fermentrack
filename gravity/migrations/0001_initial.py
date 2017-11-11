# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-10-21 13:45
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('app', '0006_auto_20171021_1344'),
    ]

    operations = [
        migrations.CreateModel(
            name='GravityLogPoint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gravity', models.DecimalField(decimal_places=11, max_digits=13)),
                ('temp', models.DecimalField(decimal_places=10, max_digits=13, null=True)),
                ('temp_format', models.CharField(choices=[('C', 'Celsius'), ('F', 'Fahrenheit')], default='C', max_length=1)),
                ('temp_is_estimate', models.BooleanField(default=True, help_text='Is this temperature an estimate?')),
                ('extra_data', models.CharField(blank=True, help_text='Extra data/notes about this point', max_length=255, null=True)),
                ('log_time', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ],
            options={
                'ordering': ['log_time'],
                'verbose_name': 'Gravity Log Point',
                'managed': False,
                'verbose_name_plural': 'Gravity Log Points',
            },
        ),
        migrations.CreateModel(
            name='GravityLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=255)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('format', models.CharField(default='F', max_length=1)),
                ('model_version', models.IntegerField(default=1)),
                ('display_extra_data_as_annotation', models.BooleanField(default=False, help_text='Should any extra data be displayed as a graph annotation?')),
            ],
        ),
        migrations.CreateModel(
            name='GravitySensor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Unique name for this device', max_length=48, unique=True)),
                ('temp_format', models.CharField(choices=[('C', 'Celsius'), ('F', 'Fahrenheit')], default='C', help_text='Temperature units', max_length=1)),
                ('sensor_type', models.CharField(choices=[('tilt', 'Tilt Hydrometer'), ('manual', 'Manual')], default='manual', help_text='Type of gravity sensor used', max_length=10)),
                ('logging_status', models.CharField(choices=[('active', 'Active'), ('paused', 'Paused'), ('stopped', 'Stopped')], default='stopped', help_text='Data logging status', max_length=10)),
                ('status', models.CharField(choices=[('active', 'Active, Managed by Circus'), ('unmanaged', 'Active, NOT managed by Circus'), ('disabled', 'Explicitly disabled, cannot be launched'), ('updating', 'Disabled, pending an update')], default='active', max_length=15)),
                ('active_log', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='gravity.GravityLog')),
                ('assigned_brewpi_device', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.BrewPiDevice')),
            ],
            options={
                'verbose_name': 'Gravity Sensor',
                'verbose_name_plural': 'Gravity Sensors',
            },
        ),
        migrations.AddField(
            model_name='gravitylog',
            name='device',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='gravity.GravitySensor'),
        ),
    ]