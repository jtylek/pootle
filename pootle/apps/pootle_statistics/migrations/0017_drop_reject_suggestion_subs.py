# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-28 13:11
from __future__ import unicode_literals

from django.db import migrations


SUGG_REJECT_FLAG = 9


def drop_reject_suggestion_subs(apps, schema_editor):
    subs = apps.get_model("pootle_statistics.Submission").objects.all()
    subs.filter(type=SUGG_REJECT_FLAG).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_statistics', '0016_drop_add_suggestion_subs'),
    ]

    operations = [
    ]