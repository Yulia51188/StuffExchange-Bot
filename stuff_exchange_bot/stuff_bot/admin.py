from django.contrib import admin

from .models import Profile
from .models import Stuff


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'external_id', 'tg_username', 'first_name',
        'last_name', 'contact')


@admin.register(Stuff)
class StuffAdmin(admin.ModelAdmin):
    list_display = ('description', 'profile', 'image_url', 'status_like_users')

# Register your models here.
