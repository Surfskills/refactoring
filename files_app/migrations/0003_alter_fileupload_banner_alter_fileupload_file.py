# Generated by Django 5.0.6 on 2024-07-20 21:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('files_app', '0002_remove_fileupload_tailored_video_fileupload_banner'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fileupload',
            name='banner',
            field=models.FileField(blank=True, null=True, upload_to='uploads/'),
        ),
        migrations.AlterField(
            model_name='fileupload',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='uploads/'),
        ),
    ]
