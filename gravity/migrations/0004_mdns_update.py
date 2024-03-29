# Generated by Django 3.0.13 on 2021-03-25 12:46

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gravity', '0003_ispindelconfiguration_temperature_correction'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tiltbridge',
            name='mdns_id',
            field=models.CharField(help_text="mDNS ID used by the TiltBridge to identify itself both on your network and to Fermentrack. NOTE - Prefix only - do not include '.local'", max_length=64, primary_key=True, serialize=False, validators=[django.core.validators.RegexValidator(regex='^[a-zA-Z0-9]+[a-zA-Z0-9-]+[a-zA-Z0-9]+$')]),
        ),
    ]
