#!/usr/bin/python
# -*- coding: utf-8 -*-

from rest_framework import serializers

from core.models import User, Token, Event, Seat, Reserve


class UserSerializer(serializers.HyperlinkedModelSerializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField()
    is_admin = serializers.BooleanField()
    is_active = serializers.BooleanField()
    last_login = serializers.DateTimeField(format='%d/%m/%Y %H:%M')

    class Meta:
        model = User
        fields = ('url', 'first_name', 'last_name', 'email', 'phone', 'is_admin', 'is_active', 'last_login')
        depth = 2


class TokenSerializer(serializers.HyperlinkedModelSerializer):
    hashcode = serializers.CharField()
    validity = serializers.DateField(format='%d/%m/%Y')
    validate_in = serializers.DateField(format='%d/%m/%Y')
    validate_by = serializers.HyperlinkedRelatedField(required=False, allow_null=True,
        queryset=User.objects.all(), view_name='user-detail')

    class Meta:
        model = Token
        fields = ('url', 'hashcode', 'validity', 'validate_in', 'validate_by')
        depth = 1


class EventSerializer(serializers.HyperlinkedModelSerializer):
    title = serializers.CharField()
    date = serializers.DateTimeField(format='%d/%m/%Y %H:%M')
    max_seatings = serializers.IntegerField()
    max_tickets = serializers.IntegerField()

    class Meta:
        model = Event
        fields = ('url', 'title', 'date', 'max_seatings', 'max_tickets')
        depth = 1

class SeatSerializer(serializers.HyperlinkedModelSerializer):
    row = serializers.CharField()
    column = serializers.IntegerField()
    type = serializers.ChoiceField(choices=((0, 'Balcão'), (1, 'Palco')))
    slug = serializers.CharField()
    is_reserved = serializers.BooleanField()

    class Meta:
        model = Seat
        fields = ('url', 'row', 'column', 'type', 'slug', 'is_reserved')
        depth = 1


class ReserveSerializer(serializers.HyperlinkedModelSerializer):
    alumn = serializers.HyperlinkedRelatedField(required=False, allow_null=True, queryset=User.objects.all(), view_name='user-detail')
    event = serializers.HyperlinkedRelatedField(required=False, allow_null=True, queryset=Event.objects.all(), view_name='event-detail')
    seats = serializers.HyperlinkedRelatedField(many=True, queryset=Seat.objects.all(), view_name='seat-detail')

    class Meta:
        model = Reserve
        fields = ('url', 'alumn', 'event', 'seats')
        depth = 2
