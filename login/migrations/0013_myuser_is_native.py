# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2018-05-22 16:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("login", "0012_auto_20180522_1621")]

    operations = [
        migrations.AddField(
            model_name="myuser",
            name="is_native",
            field=models.BooleanField(default=False),
        )
    ]
