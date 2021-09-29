from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin, BaseUserManager
from django.utils import timezone


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
    email = models.EmailField(verbose_name='email', max_length=255, unique=True)
    username = models.CharField(max_length=8, verbose_name='Username')
    is_active = models.BooleanField(default=True)

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
