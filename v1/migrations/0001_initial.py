# Generated by Django 3.2.7 on 2021-11-09 18:33

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import v1.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('primaryKey', models.BigAutoField(db_column='pk', primary_key=True, serialize=False, verbose_name='pk')),
                ('style', models.CharField(max_length=10, null=True, verbose_name="user's style")),
                ('email', models.EmailField(max_length=255, unique=True, verbose_name='email')),
                ('username', models.CharField(default='익명', max_length=8, verbose_name='user name')),
                ('profileImgURL', models.ImageField(default='v1/default/profile.jpg', null=True, upload_to='v1', verbose_name='profile Image')),
                ('is_active', models.BooleanField(default=True)),
                ('passwd', models.CharField(max_length=100, verbose_name='tempUserPasswd')),
                ('targetTime', models.IntegerField(default=0)),
                ('isTimerRunning', models.BooleanField(blank=True, default=False, verbose_name='Timer running checker Flag')),
                ('timerStartTime', models.DateTimeField(blank=True, null=True, verbose_name='Current Timer StartedTime')),
                ('newMail', models.EmailField(max_length=255, null=True, verbose_name='New Mail')),
                ('authCode', models.CharField(max_length=8, null=True, verbose_name='New Mail registrations auth field')),
                ('requestTime', models.DateTimeField(null=True, verbose_name='New Mail RequestedTime')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
            managers=[
                ('objects', v1.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Daily',
            fields=[
                ('primaryKey', models.AutoField(db_column='pk', primary_key=True, serialize=False, verbose_name='pk')),
                ('date', models.DateField(default=django.utils.timezone.now, verbose_name='Date')),
                ('goal', models.IntegerField(default=0, verbose_name='Daily goal (sec)')),
                ('totalStudyTime', models.IntegerField(default=0)),
                ('memo', models.TextField(default='')),
                ('userInfo', models.ForeignKey(db_column='userEmail', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_daily', to=settings.AUTH_USER_MODEL, verbose_name='Information of Daily')),
            ],
        ),
        migrations.CreateModel(
            name='dailySubject',
            fields=[
                ('primaryKey', models.BigAutoField(db_column='pk', primary_key=True, serialize=False, verbose_name='pk')),
                ('title', models.CharField(default='기타', max_length=15, verbose_name='Subject Name')),
                ('color', models.CharField(default='#5F79D3', max_length=7, verbose_name="Subject's personal Color")),
                ('time', models.IntegerField(default=0, verbose_name='StudyTime - second')),
                ('dateAndUser', models.ForeignKey(db_column='dailyObject', on_delete=django.db.models.deletion.CASCADE, related_name='dateAndUser', to='v1.daily')),
            ],
        ),
        migrations.CreateModel(
            name='emailAuth',
            fields=[
                ('mail', models.EmailField(max_length=255, primary_key=True, serialize=False, unique=True, verbose_name='Mail Sender')),
                ('authCode', models.CharField(max_length=8, verbose_name='Auth')),
                ('requestTime', models.DateTimeField(default=django.utils.timezone.now, verbose_name='RequestedTime')),
            ],
        ),
        migrations.CreateModel(
            name='userSubject',
            fields=[
                ('primaryKey', models.BigAutoField(db_column='pk', primary_key=True, serialize=False, verbose_name='pk')),
                ('title', models.CharField(default='기타', max_length=15, verbose_name='Subject Name')),
                ('color', models.CharField(default='#5F79D3', max_length=7, verbose_name="Subject's personal Color")),
                ('user', models.ForeignKey(db_column='user', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_subject', to=settings.AUTH_USER_MODEL, verbose_name='User info')),
            ],
        ),
        migrations.CreateModel(
            name='todoList',
            fields=[
                ('primaryKey', models.BigAutoField(db_column='pk', primary_key=True, serialize=False, verbose_name='pk')),
                ('isItDone', models.BooleanField(default=False)),
                ('todo', models.TextField(default='')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subject', to='v1.dailysubject')),
            ],
        ),
        migrations.CreateModel(
            name='post',
            fields=[
                ('primaryKey', models.BigAutoField(db_column='pk', primary_key=True, serialize=False, verbose_name='pk')),
                ('postTime', models.DateTimeField(default=django.utils.timezone.now)),
                ('startDate', models.DateField()),
                ('endDate', models.DateField()),
                ('calendarType', models.CharField(max_length=6)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='like',
            fields=[
                ('primaryKey', models.BigAutoField(db_column='pk', primary_key=True, serialize=False, verbose_name='pk')),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='v1.post')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('groupCode', models.CharField(max_length=8, primary_key=True, serialize=False, unique=True, verbose_name='code')),
                ('userCount', models.IntegerField(default=1)),
                ('leaderUser', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='leader', to=settings.AUTH_USER_MODEL)),
                ('user', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='comment',
            fields=[
                ('primaryKey', models.BigAutoField(db_column='pk', primary_key=True, serialize=False, verbose_name='pk')),
                ('postTime', models.DateTimeField(default=django.utils.timezone.now)),
                ('content', models.TextField(default='')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='v1.post')),
            ],
        ),
        migrations.AddField(
            model_name='user',
            name='timerRunningSubject',
            field=models.OneToOneField(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='timerRunningSubject', to='v1.usersubject', verbose_name='Timer Running Subject'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions'),
        ),
    ]
