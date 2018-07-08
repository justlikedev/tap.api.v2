#!/usr/bin/python
# -*- coding: utf-8 -*-

import hashlib
import locale
from datetime import datetime

import pytz
from django.utils import timezone
from rest_framework import permissions as rf_permissions
from rest_framework import status, viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from core.controllers import render, render_to_pdf, send_mail
from core.models import Event, Reserve, Seat, Token, User
from rest.serializers import (EventSerializer, ReserveSerializer,
                              SeatSerializer, TokenSerializer, UserSerializer)

TZ = pytz.timezone('America/Sao_Paulo')
locale.setlocale(locale.LC_TIME, 'pt_BR.utf8')

class UserViewSet(viewsets.ModelViewSet):
    """
    API view set to handle users.

    Examples:

        GET /api/users/ - show all users
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (rf_permissions.IsAuthenticated, rf_permissions.IsAdminUser)


class TokenViewSet(viewsets.ModelViewSet):
    """
    API view set to handle tokens.

    Examples:

        GET /api/tokens/ - show all tokens
    """
    queryset = Token.objects.all()
    serializer_class = TokenSerializer
    permission_classes = (rf_permissions.IsAuthenticated, rf_permissions.IsAdminUser)


class EventViewSet(viewsets.ModelViewSet):
    """
    API view set to handle events.

    Examples:

        GET  /api/events/         - show all events

    Extra actions:

        POST /api/events/id/clone - clone an event for other date
    """


    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = (rf_permissions.IsAuthenticatedOrReadOnly, )

    @detail_route(methods=['post', 'get'], permission_classes=[rf_permissions.IsAuthenticated, rf_permissions.IsAdminUser], url_path='clone')
    def clone(self, request, pk):
        """
        Clone an event for other date
        """

        # TODO is only for tests using browsable api and should be removed before send to production
        if request.method == 'GET':
            return Response(data='OK', status=status.HTTP_200_OK)

        new_date = request.data.get('date')

        if not new_date:
            raise ValidationError('Nova data não informada.')

        try:
            event = Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            raise NotFound('Evento não encontrado ou não existe.')

        Event.objects.create(title='{0} cópia'.format(event.title), date=new_date, 
            max_seatings=event.max_seatings, max_tickets=event.max_tickets)

        return Response(data={'success': 'Evento clonado com sucesso.'}, status=status.HTTP_201_CREATED)


class SeatViewSet(viewsets.ModelViewSet):
    """
    API view set to handle seats.

    Examples:

        GET /api/seats/ - show all seats
    """
    queryset = Seat.objects.all()
    serializer_class = SeatSerializer
    permission_classes = (rf_permissions.IsAuthenticatedOrReadOnly, )


class ReserveViewSet(viewsets.ModelViewSet):
    """
    API view set to handle reservations.

    Examples:

        GET  /api/reservations/                       - show all reservations

    Extra actions:

        POST /api/reservations/add-seat               - add seats to reserve
        POST /api/reservations/id/cancel              - cancel a reserve
        POST /api/reservations/id/finish              - finish a reserve
        POST /api/reservations/id/paid                - confirm a reserve was paid
        POST /api/reservations/id/send-confirmation   - send a reserve confirmation
        GET  /api/reservations/id/view-confirmation   - view a reserve confirmation
    """
    queryset = Reserve.objects.all()
    serializer_class = ReserveSerializer
    permission_classes = (rf_permissions.IsAuthenticatedOrReadOnly, )

    @staticmethod
    def check_available_tickets(reserve, max_tickets):
        """
        check if has available tickets for this alumn
        """

        tickets = reserve.seats.count()
        check = tickets < max_tickets

        if check:
            available = max_tickets - tickets
            return check, available

        return check, 0

    @staticmethod
    def is_session_valid(reserve):
        limit = reserve.updated_at.minute + (int(reserve.session.total_seconds() / 60) % 60)
        now = timezone.localtime(timezone.now(), timezone=TZ).minute

        # if limit is not greater than now, the reserve should be deleted and seats released
        if limit < now:
            reserve.delete()
            raise ValidationError('Sua sessão expirou e sua reserva não foi finalizada. Escolha novos assentos para continuar.')

        # if limit is greater than now the session is available
        return True

    @staticmethod
    def create_hash():
        code = hashlib.sha1()
        code.update(str(datetime.now()))
        return code.hexdigest()[:10].upper()

    @staticmethod
    def get_confirmation_context(pk):
        try:
            reserve = Reserve.objects.get(pk=pk)
        except Reserve.DoesNotExist:
            raise NotFound('Reserva não encontrada')

        seats = []
        for seat in reserve.seats.all():
            seats.append(seat.slug)

        return {
            'alumn_name': reserve.alumn.get_full_name,
            'alumn_email': reserve.alumn.email,
            'event_title': reserve.event.title,
            'event_date': reserve.event.slug_date,
            'event_hour': reserve.event.slug_hour,
            'seats': seats,
            'code': reserve.code
        }

    @list_route(methods=['post', 'get'], permission_classes=[rf_permissions.IsAuthenticated], url_path='add-seat')
    def add_seat(self, request):
        """
        create reserve or add seats to exist reserve
        """

        # TODO is only for tests using browsable api and should be removed before send to production
        if request.method == 'GET':
            return Response(data='OK', status=status.HTTP_200_OK)

        seat_id = request.data.get('seat')
        event_id = request.data.get('event')
        alumn = request.user

        try:
            event = Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            raise NotFound('Evento não encontrado.')

        try:
            seat = Seat.objects.get(pk=seat_id)
        except Seat.DoesNotExist:
            raise NotFound('Assento não encontrado.')

        reserve = Reserve.objects.filter(event_id=event_id, alumn=alumn)
        if reserve.exists():  # add seat to reserve
            reserve = reserve.get()
            self.is_session_valid(reserve)
            available = self.check_available_tickets(reserve, event.max_tickets)
            if available[0]:
                reserve.seats.add(seat)
                reserve.save()
            else:
                return Response(data={'error': 'Você selecionou o máximo de assentos disponíveis ({0}) para sua reserva.'.format(event.max_tickets),
                                      'info': 'Você deve finalizar sua reserva para confirmá-la e garantir seus assentos ou desmarcar um dos assentos selecionados.'},
                                status=status.HTTP_300_MULTIPLE_CHOICES)
        else:  # create the reserve
            created = Reserve.objects.create(alumn=alumn, event=event)
            created.seats.add(seat)
            created.save()

        return Response(data={'success': 'O assento {0} foi adicionado a sua reserva.'.format(seat.slug),
                              'info': 'Tempo de sessão atualizado para 20 minutos.',
                              'available_tickets': available[1] - 1},
                        status=status.HTTP_200_OK)

    @detail_route(methods=['post', 'get'], permission_classes=[rf_permissions.IsAuthenticated, rf_permissions.IsAdminUser], url_path='cancel')
    def cancel(self, request, pk):
        """
        cancel reserve and release the seats
        """

        # TODO is only for tests using browsable api and should be removed before send to production
        if request.method == 'GET':
            return Response(data='OK', status=status.HTTP_200_OK)

        cancel = request.data.get('cancel')

        if not cancel:
            raise ValidationError('Parâmetro \'cancel\' não informado.')

        try:
            Reserve.objects.filter(pk=pk).delete()
        except Reserve.DoesNotExist: 
            raise NotFound('Reserva não encontrada')

        return Response(data={'success': 'Reserva foi cancelada com sucesso.'}, status=status.HTTP_200_OK)

    @detail_route(methods=['post', 'get'], permission_classes=[rf_permissions.IsAuthenticated, rf_permissions.IsAdminUser], url_path='finish')
    def finish(self, request, pk):
        """
        finish the reserve
        """

        # TODO is only for tests using browsable api and should be removed before send to production
        if request.method == 'GET':
            return Response(data='OK', status=status.HTTP_200_OK)

        finished = request.data.get('finished')

        if not finished:
            raise ValidationError('Parâmetro \'finished\' não informado.')

        try:
            reserve = Reserve.objects.get(pk=pk)
        except Reserve.DoesNotExist: 
            raise NotFound('Reserva não encontrada')

        reserve.finished = True
        reserve.code = self.create_hash()
        reserve.save()

        return Response(data={'success': 'Solicitação de reserva concluída.',
                              'info': 'Após a confirmação do pagamento você poderá imprimir seu comprovante de reserva.'}, 
                        status=status.HTTP_200_OK)

    @detail_route(methods=['post', 'get'], permission_classes=[rf_permissions.IsAuthenticated, rf_permissions.IsAdminUser], url_path='paid')
    def paid(self, request, pk):
        """
        confirm payment received
        """

        # TODO is only for tests using browsable api and should be removed before send to production
        if request.method == 'GET':
            return Response(data='OK', status=status.HTTP_200_OK)

        paid = request.data.get('paid')

        if not paid:
            raise ValidationError('Parâmetro \'paid\' não informado.')

        try:
            reserve = Reserve.objects.get(pk=pk)
        except Reserve.DoesNotExist:
            raise NotFound('Reserva não encontrada')

        reserve.paid = True
        reserve.save()

        return Response(data={'success': 'Pagamento confirmado.'}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'], permission_classes=[rf_permissions.IsAuthenticated, rf_permissions.IsAdminUser], url_path='view-confirmation')
    def get_confirmation(self, request, pk):
        context = self.get_confirmation_context(pk)
        return render_to_pdf('booking-confirmation.html', context)

    @detail_route(methods=['get'], permission_classes=[rf_permissions.IsAuthenticated, rf_permissions.IsAdminUser], url_path='send-confirmation')
    def send_confirmation_mail(self, request, pk):
        context = self.get_confirmation_context(pk)
        error = send_mail(template_src='emails/booking-confirmation.html', context=context, 
            mail_from='no-reply@gmail.com', mail_to='rdgsdev@gmail.com')

        if not error:
            return Response(data={'success': 'Confirmação de Reserva enviada.'}, status=status.HTTP_200_OK)

