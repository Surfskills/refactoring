# Generated by Django 5.0.6 on 2024-07-18 21:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0004_rename_name_user_full_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='full_name',
        ),
    ]