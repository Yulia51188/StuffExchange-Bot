# Generated by Django 3.2.7 on 2021-09-27 08:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stuff_bot', '0008_stuff_status_like_users'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='contact',
            field=models.CharField(blank=True, default='', max_length=256, verbose_name='Контакт для связи'),
        ),
        migrations.AddField(
            model_name='profile',
            name='first_name',
            field=models.CharField(blank=True, default='', max_length=256, verbose_name='Имя пользователя в Телеграме'),
        ),
        migrations.AddField(
            model_name='profile',
            name='last_name',
            field=models.CharField(blank=True, default='', max_length=256, verbose_name='Имя пользователя в Телеграме'),
        ),
        migrations.AddField(
            model_name='profile',
            name='tg_username',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='Имя пользователя в Телеграме'),
        ),
        migrations.AlterField(
            model_name='stuff',
            name='profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stuff_bot.profile', verbose_name='Профиль'),
        ),
    ]