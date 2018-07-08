#!/usr/bin/python
# -*- coding: utf-8 -*-


from datetime import datetime, timedelta

import pytz

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils import timezone

from core.managers import UserManager

TZ = pytz.timezone('America/Sao_Paulo')


class User(AbstractBaseUser, PermissionsMixin):
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(max_length=150, unique=True, validators=[username_validator])
    first_name = models.CharField(max_length=100, null=True)
    last_name = models.CharField(max_length=100, null=True)
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )
    phone = models.CharField(max_length=15, null=False)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'

    objects = UserManager()

    class Meta:
        verbose_name = u'User'
        verbose_name_plural = u'Users'

    def get_full_name(self):
        return u'{0} {1}'.format(self.first_name, self.last_name)

    def get_short_name(self):
        return self.first_name

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True


class Token(models.Model):
    hashcode = models.CharField(max_length=10, null=False)
    validity = models.DateField(null=True)
    validate_in = models.DateField(null=True)
    validate_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

    objects = models.Manager()

    class Meta:
        verbose_name = 'Token'
        verbose_name_plural = 'Tokens'

    def __unicode__(self):
        return 'Token: {0}, {1}'.format(self.hashcode, self.validity)


class Event(models.Model):
    title = models.CharField(max_length=200, null=False)
    date = models.DateTimeField(null=False)
    max_seatings = models.IntegerField(null=True)  # define quantidade máxima de assentos
    max_tickets = models.IntegerField(null=True)   # define quantidade máxima de tickets por aluno

    objects = models.Manager()

    class Meta:
        verbose_name = 'Event'
        verbose_name_plural = 'Events'

    def __unicode__(self):
        return 'Event: {0}, {1}'.format(self.title, self.date)

    @property
    def slug_date(self):  # 20 DEZ
        return self.date.strftime('%d %b')

    @property
    def slug_hour(self):  # 20:00
        return self.date.strftime('%H:%M')


class Seat(models.Model):
    row = models.CharField(max_length=10, null=False)
    column = models.CharField(max_length=10, null=False)
    type = models.CharField(max_length=1, null=True)  # 0 = Balcão / 1 = Palco

    objects = models.Manager()

    @property
    def slug(self):
        return '{0} {1}{2}'.format('Balcão' if self.type == 0 else 'Palco', self.row, self.column)

    @property
    def is_reserved(self):
        return Reserv.objects.filter(seats__id=self.id).exists()

    @property
    def type_name(self):
        return 'Balcão' if self.type is 0 else 'Palco'

    class Meta:
        verbose_name = 'Seat'
        verbose_name_plural = 'Seats'

    def __unicode__(self):
        return 'Seat: {0} - {1}'.format(self.row, self.column)


class Reserv(models.Model):
    alumn = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    event = models.ForeignKey(Event, null=True, on_delete=models.SET_NULL)
    seats = models.ManyToManyField(Seat)
    is_paid = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now_add=timezone.localtime(timezone.now(), timezone=TZ))
    session = models.DurationField(default=timedelta(minutes=20))
    code = models.CharField(max_length=10, null=True)

    objects = models.Manager()

    class Meta:
        verbose_name = 'Reserv'
        verbose_name_plural = 'Reservs'

    def __unicode__(self):
        return 'Reserv: {0} reserved for: {1}'.format(self.event, self.alumn)

    def save(self, *args, **kwargs):
        # refresh the field update_at
        self.updated_at = timezone.localtime(timezone.now(), timezone=TZ)
        super(Reserv, self).save(*args, **kwargs)
