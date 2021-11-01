from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import User
from .models import Daily

class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ('email', 'username', 'isTimerRunning')
    list_filter = ('email', 'username', 'isTimerRunning')
    fieldsets = (
        (None, {"fields": ('email', 'password', 'profileImgURL')}),
        ('Personal Info', {'fields': ('username', 'date_joined')}),
        ('Status Info', {'fields': ('isTimerRunning',)}),
        # ('Daily works', {'fields': ('dailyInfo',)}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'is_active')})
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_staff', 'is_superuser')}
        ),
    )
    search_fields = ('email', 'username')
    ordering = ('email',)
    filter_horizontal = ()

class DailyAdmin(admin.ModelAdmin):
    list_display = ('userInfo', 'date')
    list_filter = ('userInfo', 'date')
    fieldsets = (
        (None, {"fields": ('userInfo',)}),
        ('Daily Information')
    )

# class SubjectAdmin(admin.ModelAdmin):
#     list_display = ('date', 'title')
#     list_filter = ('title')
#     fieldsets = (
#
#     )

admin.site.register(User, UserAdmin)
admin.site.register(Daily)
# admin.site.register(SubjectAdmin)
admin.site.unregister(Group)
