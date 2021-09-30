from django.utils.timezone import now
from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from .config import config as cfg

class daily(models.Model):
    userEmail = models.EmailField(verbose_name='Table Owner', primary_key=True, null=False, default='')
    # date = models.DateField(default=now, verbose_name='Date', null=False)
    # goal = models.IntegerField(default=0, verbose_name='Daily goal (sec)', blank=False, null=False)

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('No Email.')
        email = self.normalize_email(email)
        user = self.model(email=email, password=password, **extra_fields)
        user.set_password(password)
        user.save(using=self.db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Administrator must be 'is_staff' is True")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Administrator must be 'is_superuser' is True")

        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    objects = UserManager()
    id = models.AutoField(primary_key=True)
    style = models.CharField(max_length=10, verbose_name='user\'s style', null=True)
    email = models.EmailField(verbose_name='email', max_length=255, unique=True)
    username = models.CharField(max_length=8, verbose_name='user name')
    profileImg = models.URLField(verbose_name='profile Image URL', default=cfg.DEFAULT_PROFILE_IMG)
    is_active = models.BooleanField(default=True)
    dailyInfo = models.OneToOneField(daily, on_delete=models.CASCADE, null=True, verbose_name='Information of Daily')

    # EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    date_joined = models.DateTimeField('date joined', default=timezone.now)

    def __str__(self):
        return self.email

    def get_short_name(self):
        return self.username

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
