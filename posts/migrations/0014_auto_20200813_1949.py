# Generated by Django 2.2.6 on 2020-08-13 16:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0013_auto_20200805_1707'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ('-created',)},
        ),
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ('-pub_date',)},
        ),
    ]
