#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import random
import string
from datetime import datetime

import pytz
from dateutil.relativedelta import relativedelta

from core.models import Event, Reserv, Seat, Token, User

TZ = pytz.timezone('America/Sao_Paulo')


def create_tokens(quantity=100):
    for token in range(0, quantity):
        hashcode = random.getrandbits(32)
        validity = (datetime.now() + relativedelta(days=15)).date()
        Token.objects.create(hashcode=hashcode, validity=validity)
        print('{0} token created: {1} validity until {2}'.format(token, hashcode, validity))


def create_seats():
    # create seats for stage
    print('seats for stage')
    for row in string.ascii_letters.upper()[0:20]:
        if row == 'A':
            columns = list(range(1, 27))
        elif row in ('S', 'T'):
            columns = list(range(5, 29))
        else:
            columns = list(range(1, 29))
        for column in columns:
            print('seat {0}{1}'.format(row, column))
            Seat.objects.create(type=1, row=row, column=column)

    # create seats for balcon
    print('seats for balcon')
    for row in string.ascii_letters.upper()[0:14]:
        columns = list(range(1, 30))
        if row in ('A', 'B', 'C', 'D', 'E', 'F'):
            columns = list(range(9, 30))
        elif row in ('G', 'H', 'I', 'J'):
            columns = list(range(1, 30))
        elif row == 'K':
            columns.remove(28)
        elif row == 'L':
            columns.remove(28)
            columns.remove(26)
            columns.remove(24)
        elif row in ('M', 'N'):
            columns.remove(28)
            columns.remove(26)
            columns.remove(24)
            columns.remove(22)
        for column in columns:
            print('seat {0}{1}'.format(row, column))
            Seat.objects.create(type=0, row=row, column=column)

def populate():
    # clearing database
    User.objects.all().delete()
    Token.objects.all().delete()
    Event.objects.all().delete()
    Seat.objects.all().delete()
    Reserv.objects.all().delete()

    # create tokens
    print('creating some tokens')
    create_tokens()

    # create seats
    print('creating some seats')
    create_seats()

    # create a superuser
    print('creating a superuser admin@tap.com / tapacademy')
    admin = User.objects.create_superuser(email='admin@tap.com', password='tapacademy', first_name='Admin', username='admin')

    # create alumns
    print('creating some alumns with passwords <name>123')
    luigi = User.objects.create_user(first_name='Luigi', password='luigi123', email='luigi@tap.com', username='luigi')
    mario = User.objects.create_user(first_name='Mario', password='mario123', email='mario@tap.com', username='mario')
    User.objects.create_user(first_name='Peach', password='peach123', email='peach@tap.com', username='peach')
    User.objects.create_user(first_name='Yoshi', password='yoshi123', email='yoshi@tap.com', username='yoshi')

    # create events
    print('creating some events')
    event_1 = Event.objects.create(title='A princesa Peach no reino encantado do sapateado.',
        date=datetime(2018, 12, 10, 20, tzinfo=TZ), max_seatings=100, max_tickets=3)

    print('%s created' % event_1.title)

    event_2 = Event.objects.create(title='Mario e Luigi salvam a princesa Peach sapateando.',
        date=datetime(2018, 12, 10, 20, tzinfo=TZ), max_seatings=100, max_tickets=3)

    print('%s created' % event_2.title)

    # create reservations
    print('creating some reservations')

    reserv = Reserv.objects.create(alumn=mario, event=event_1)
    reserv.seats.add(Seat.objects.filter(row='A', column='9', type='0').get())
    reserv.seats.add(Seat.objects.filter(row='A', column='11', type='0').get())
    reserv.seats.add(Seat.objects.filter(row='A', column='13', type='0').get())
    reserv.save()

    reserv = Reserv.objects.create(alumn=luigi, event=event_2)
    reserv.seats.add(Seat.objects.filter(row='F', column='18', type='1').get())
    reserv.seats.add(Seat.objects.filter(row='F', column='16', type='1').get())
    reserv.seats.add(Seat.objects.filter(row='F', column='14', type='1').get())
    reserv.save()

if __name__ == "__main__":
    populate()
