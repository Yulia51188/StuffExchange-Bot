# Generated by Django 3.2.7 on 2021-09-27 08:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stuff_bot', '0010_auto_20210927_0840'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='name',
        ),
        migrations.AlterField(
            model_name='profile',
            name='first_name',
            field=models.CharField(blank=True, default='', max_length=256, verbose_name='Имя'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='last_name',
            field=models.CharField(blank=True, default='', max_length=256, verbose_name='Фамилия'),
        ),
    ]