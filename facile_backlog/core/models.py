from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from ..util import gravatar_url


class UserManager(BaseUserManager):
    @classmethod
    def normalize_email(cls, email):
        email = email or ''
        return email.lower()

    def create_user(self, email, password=None, **extra_fields):
        now = timezone.now()
        if not email:
            raise ValueError(_('The email must be set.'))
        email = UserManager.normalize_email(email)
        user = self.model(email=email, last_login=now, date_joined=now,
                          **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        user = self.create_user(email, password, **extra_fields)
        user.is_staff = True
        user.is_active = True
        user.is_superuser = True
        user.save(using=self._db, update_fields=['is_staff', 'is_active',
                                                 'is_superuser'])
        return user


class User(AbstractBaseUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    email = models.EmailField(_('Email address'), max_length=255,
                              unique=True, db_index=True)
    full_name = models.CharField(_('Full name'), max_length=1023, blank=True)
    is_staff = models.BooleanField(_('Staff status'), default=False)
    is_active = models.BooleanField(_('Active'), default=False)
    is_superuser = models.BooleanField(_('Superuser status'), default=False)
    date_joined = models.DateTimeField(_('Date joined'), default=timezone.now)
    lang = models.CharField(_("Language"), max_length=3, blank=True,
                            choices=settings.LANGUAGES)
    objects = UserManager()

    @property
    def username(self):
        # WebTest's middleware assumes we have a username field
        return self.email

    def get_full_name(self):
        return self.full_name
    get_short_name = get_full_name

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    def get_gravatar_url(self, size=32):
        return gravatar_url(self.email, size)

    def get_mini_gravatar_url(self):
        return gravatar_url(self.email, 24)
