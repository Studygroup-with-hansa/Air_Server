from django.utils.timezone import now
from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from .config import config as cfg


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password=None, username='익명', **extra_fields):
        if not email:
            raise ValueError('No Email.')
        email = self.normalize_email(email)
        user = self.model(email=email, password=password, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self.db)
        return user

    def create_user(self, email, password=None, username='익명', **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, username, **extra_fields)

    def create_superuser(self, email, password, username='Admin', **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Administrator must be 'is_staff' is True")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Administrator must be 'is_superuser' is True")

        return self._create_user(email, password, username, **extra_fields)


class userSubject(models.Model):
    # date = models.ForeignKey("Daily", related_name='daily', on_delete=models.CASCADE, null=True, verbose_name='Date info', db_column="date")
    primaryKey = models.BigAutoField(verbose_name='pk', db_column='pk', primary_key=True)
    user = models.ForeignKey("User", related_name='user_subject', on_delete=models.CASCADE, null=True, verbose_name='User info', db_column="user")
    title = models.CharField(default='기타', verbose_name='Subject Name', null=False, max_length=15)
    color = models.CharField(default=cfg.DEFAULT_SUBJECT_COLOR, verbose_name="Subject's personal Color", null=False, max_length=7)
    # time = models.IntegerField(default=0, verbose_name='Study time - second', null=False)
    # startTime = models.DateTimeField(verbose_name='LastTimerStartedTime', null=True)


class dailySubject(models.Model):
    primaryKey = models.BigAutoField(verbose_name='pk', db_column='pk', primary_key=True)
    dateAndUser = models.ForeignKey("Daily", related_name='dateAndUser', db_column="dailyObject", on_delete=models.CASCADE)
    title = models.CharField(default='기타', verbose_name='Subject Name', null=False, max_length=15)
    color = models.CharField(default=cfg.DEFAULT_SUBJECT_COLOR, max_length=7, verbose_name="Subject's personal Color", null=False)
    time = models.IntegerField(default=0, verbose_name="StudyTime - second", null=False)


class todoList(models.Model):
    primaryKey = models.BigAutoField(verbose_name='pk', db_column='pk', primary_key=True)
    subject = models.ForeignKey("dailySubject", related_name='subject', on_delete=models.CASCADE)
    isItDone = models.BooleanField(default=False, null=False)
    todo = models.TextField(default='', null=False)


class Daily(models.Model):
    userInfo = models.ForeignKey("User", related_name='user_daily', on_delete=models.CASCADE, null=True, verbose_name='Information of Daily', db_column="userEmail")
    date = models.DateField(default=now, verbose_name='Date', null=False, primary_key=True)
    goal = models.IntegerField(default=0, verbose_name='Daily goal (sec)', blank=False, null=False)
    totalStudyTime = models.IntegerField(default=0, null=False)
    memo = models.TextField(default='', null=False)


class emailAuth(models.Model):
    mail = models.EmailField(verbose_name='Mail Sender', max_length=255, unique=True, primary_key=True)
    authCode = models.CharField(verbose_name='Auth', max_length=8)
    requestTime = models.DateTimeField(verbose_name='RequestedTime', default=timezone.now)


class User(AbstractUser):
    objects = UserManager()
    primaryKey = models.BigAutoField(verbose_name='pk', db_column='pk', primary_key=True)
    # id = models.AutoField(primary_key=True, null=False)
    style = models.CharField(max_length=10, verbose_name='user\'s style', null=True)
    email = models.EmailField(verbose_name='email', max_length=255, unique=True, primary_key=False)
    username = models.CharField(max_length=8, verbose_name='user name', default='익명', null=False)
    profileImgURL = models.URLField(verbose_name='profile Image URL', default=cfg.DEFAULT_PROFILE_IMG)
    is_active = models.BooleanField(default=True)
    passwd = models.CharField(verbose_name='tempUserPasswd', max_length=100)

    targetTime = models.IntegerField(default=0, null=False)

    isTimerRunning = models.BooleanField(default=False, null=False, verbose_name='Timer running checker Flag', blank=True)
    timerRunningSubject = models.OneToOneField(userSubject, default=None, null=True, verbose_name='Timer Running Subject', on_delete=models.SET_DEFAULT, related_name='timerRunningSubject', blank=True)
    timerStartTime = models.DateTimeField(null=True, verbose_name='Current Timer StartedTime', blank=True)

    newMail = models.EmailField(verbose_name='New Mail', max_length=255, null=True)
    authCode = models.CharField(verbose_name='New Mail registrations auth field', max_length=8, null=True)
    requestTime = models.DateTimeField(verbose_name='New Mail RequestedTime', null=True)


    # EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    date_joined = models.DateTimeField('date joined', default=timezone.now)

    def __str__(self):
        return self.email

    def get_short_name(self):
        return self.username

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'


class Group(models.Model):
    groupCode = models.CharField(max_length=8, verbose_name='code', null=False, primary_key=True, unique=True)
    leaderUser = models.OneToOneField('User', related_name='leader', on_delete=models.CASCADE, null=False)
    userCount = models.IntegerField(default=1, null=False)
    user = models.ManyToManyField(User)


class post(models.Model):
    primaryKey = models.BigAutoField(verbose_name='pk', db_column='pk', primary_key=True)
    author = models.ForeignKey("User", on_delete=models.CASCADE)
    postTime = models.DateTimeField(default=timezone.now)
    startDate = models.DateField()
    endDate = models.DateField()
    calendarType = models.CharField(max_length=6)
    likeCount = models.IntegerField(default=0, null=False)
    achievement = models.TextField(default='', null=False)      # Separate with |


class comment(models.Model):
    primaryKey = models.BigAutoField(verbose_name='pk', db_column='pk', primary_key=True)
    post = models.ForeignKey("post", on_delete=models.CASCADE)
    author = models.ForeignKey("User", on_delete=models.CASCADE)
    postTime = models.DateTimeField(default=timezone.now)
    content = models.TextField(default='', null=False)


class like(models.Model):
    primaryKey = models.BigAutoField(verbose_name='pk', db_column='pk', primary_key=True)
    post = models.ForeignKey("post", on_delete=models.CASCADE)
    user = models.ForeignKey("User", on_delete=models.CASCADE)
