# Generated by Django 2.1.2 on 2018-10-25 18:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('channel', '0002_remove_user_password'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='user_id',
        ),
    ]
