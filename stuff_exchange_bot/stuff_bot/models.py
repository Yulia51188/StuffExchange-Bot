import jsonfield
from django.db import models


class Profile(models.Model):
    external_id = models.PositiveIntegerField(
        verbose_name='Внешний ID пользователя',
        unique=True,
    )
    name = models.TextField(
        verbose_name='Имя пользователя',
    )

    def __str__(self):
        return f'{self.name}'

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'


class Stuff(models.Model):
    profile = models.ForeignKey(
        to='stuff_bot.Profile',
        verbose_name='Профиль',
        on_delete=models.PROTECT,
    )
    description = models.CharField(max_length=256)

    image_url = models.CharField(max_length=256)

    status_like = models.BooleanField(default=False, verbose_name='Нравится')
    status_like_users = jsonfield.JSONField(default=False)
    
    class Meta:
        verbose_name = 'Вещь'
        verbose_name_plural = 'Вещи'
