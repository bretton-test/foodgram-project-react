from django.contrib import admin

from .models import Follow, User


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    list_display_links = ('user',)
    list_filter = ('user',)
    search_fields = ('user', 'author')


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_filter = ('username', 'email')
    search_fields = ('username', 'email')
