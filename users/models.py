from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone  
import uuid


class UserManager(BaseUserManager):

    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        if not username:
            raise ValueError('Username обязателен')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('dashboard_role', 'superadmin')
        return self.create_user(email, username, password, **extra_fields)



class User(AbstractBaseUser, PermissionsMixin):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, default='')

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    
    DASHBOARD_ROLES = [
        ('superadmin', 'Superadmin'),
        ('moderator', 'Moderator'),
        ('analyst', 'Analyst'),
    ]
    dashboard_role = models.CharField(
        max_length=20,
        choices=DASHBOARD_ROLES,
        blank=True,
        default='',
    )

   
    push_enabled = models.BooleanField(default=True)
    push_token = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email



class Profile(models.Model):

    UI_LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('en', 'English'),
        ('tg', 'Тоҷикӣ'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    full_name = models.CharField(max_length=150, blank=True, default='')
    avatar_url = models.URLField(blank=True, default='')
    bio = models.TextField(max_length=500, blank=True, default='')

    native_language = models.CharField(max_length=10, blank=True, default='')
    timezone = models.CharField(max_length=50, default='UTC')
    ui_language = models.CharField(
        max_length=5,
        choices=UI_LANGUAGE_CHOICES,
        default='ru',
    )

    
    telegram_chat_id = models.CharField(max_length=50, blank=True, default='')

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'profiles'
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return f'Профиль — {self.user.email}'



class EmailVerification(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verifications')
    code = models.CharField(max_length=6)

    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'email_verifications'
        verbose_name = 'Код подтверждения email'
        verbose_name_plural = 'Коды подтверждения email'

    def __str__(self):
        return f'{self.user.email} — {self.code}'

    @property
    def is_expired(self):
        return self.expires_at < timezone.now()



class Friendship(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('accepted', 'Принят'),
        ('rejected', 'Отклонён'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='friend_requests_sent',
    )
    to_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='friend_requests_received',
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'friendships'
        verbose_name = 'Дружба'
        verbose_name_plural = 'Дружбы'
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f'{self.from_user.username} → {self.to_user.username} ({self.status})'



class UserLanguage(models.Model):

    CEFR_CHOICES = [
        ('A1', 'A1'),
        ('A2', 'A2'),
        ('B1', 'B1'),
        ('B2', 'B2'),
        ('C1', 'C1'),
        ('C2', 'C2'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_languages')
    language_code = models.CharField(max_length=10)  # код языка из languages app
    level = models.CharField(max_length=2, choices=CEFR_CHOICES)
    show_level = models.BooleanField(default=True)  # скрывать уровень или нет

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_languages'
        verbose_name = 'Изучаемый язык'
        verbose_name_plural = 'Изучаемые языки'
        unique_together = ('user', 'language_code')

    def __str__(self):
        return f'{self.user.username} — {self.language_code} ({self.level})'