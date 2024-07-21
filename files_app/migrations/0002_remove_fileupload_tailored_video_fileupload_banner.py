# Generated by Django 5.0.6 on 2024-07-20 21:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('files_app', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fileupload',
            name='tailored_video',
        ),
        migrations.AddField(
            model_name='fileupload',
            name='banner',
            field=models.FileField(default=0, upload_to='uploads/'),
            preserve_default=False,
        ),
    ]
