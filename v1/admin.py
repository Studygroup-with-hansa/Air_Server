from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import User, Daily, emailAuth, todoList, dailySubject, userSubject
from .models import Group as Group_


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ('email', 'username', 'isTimerRunning')
    list_filter = ('email', 'username', 'isTimerRunning')
    fieldsets = (
        (None, {"fields": ('email', 'password', 'profileImgURL')}),
        ('Personal Info', {'fields': ('username', 'date_joined')}),
        ('Status Info', {'fields': ('isTimerRunning', 'timerRunningSubject', 'timerStartTime')}),
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
        (None, {"fields": ('userInfo', 'date')}),
        ('Daily Information', {'fields': ('goal', 'totalStudyTime', 'memo')})
    )
    search_fields = ('date', 'userInfo')
    ordering = ('date',)
    filter_horizontal = ()


class DailySubjectAdmin(admin.ModelAdmin):
    list_display = ('dateAndUser', 'title')
    list_filter = ('title', 'dateAndUser')
    fieldsets = (
        (None, {"fields": ('dateAndUser',)}),
        ("Subject Info", {"fields": ('title', 'color', 'time')})
    )
    search_fields = ('dateAndUser', 'title')
    ordering = ('dateAndUser',)
    filter_horizontal = ()


class emailAuthAdmin(admin.ModelAdmin):
    list_display = ('mail', 'requestTime')
    list_filter = ('mail', 'requestTime')
    fieldsets = (
        (None, {"fields": ('mail', 'requestTime', 'authCode')}),
    )
    search_fields = ('mail', 'authCode')
    ordering = ('requestTime',)
    filter_horizontal = ()


class userSubjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'user')
    list_filter = ('user', 'title')
    fieldsets = (
        (None, {"fields": ("user",)}),
        ("Subject Info", {"fields": ('title', 'color')})
    )
    search_fields = ('title', 'user')
    ordering = ('user',)
    filter_horizontal = ()


class groupAdmin(admin.ModelAdmin):
    list_display = ('groupCode', 'userCount', 'leaderUser')
    list_filter = ('groupCode', 'leaderUser', 'userCount')
    fieldsets = (
        ("Group Info", {"fields": ("groupCode",)}),
        ("User Info", {"fields": ("leaderUser", "userCount", 'user')})
    )
    search_fields = ('groupCode', 'leaderUser')
    ordering = ('userCount',)
    filter_horizontal = ()


class todoListAdmin(admin.ModelAdmin):
    list_display = ('subject', 'isItDone')
    list_filter = ('isItDone',)
    fieldsets = (
        ("TodoList Info", {"fields": ("subject", "todo", "isItDone")}),
    )
    search_fields = ("primaryKey", "isItDone",)
    ordering = ("primaryKey",)
    filter_horizontal = ()


admin.site.register(User, UserAdmin)
admin.site.register(Daily, DailyAdmin)
admin.site.register(emailAuth, emailAuthAdmin)
admin.site.register(todoList, todoListAdmin)
admin.site.register(dailySubject, DailySubjectAdmin)
admin.site.register(userSubject, userSubjectAdmin)
# admin.site.register(SubjectAdmin)
admin.site.register(Group_, groupAdmin)
admin.site.unregister(Group)
