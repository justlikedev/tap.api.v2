#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import uuid
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pdfkit
from django.http import HttpResponse
from django.template import Context, TemplateDoesNotExist
from django.template.loader import get_template
from rest_framework.exceptions import NotFound, ValidationError

from api import settings


def render_to_pdf(template_src, context={}):
    """Generate a pdf file from template

    Arguments:
        template_src {string} -- path from template

    Raises:
        ValidationError -- Indicating error on getting the template
        ValidationError -- Indicating error making pdf

    Returns:
        Response -- Response with the pdf file for download
    """

    try:
        template = get_template(template_src)
    except TemplateDoesNotExist:
        raise ValidationError('Template não encontrado.')

    html = template.render(context)
    # return HttpResponse(html)
    filepath = settings.DOC_ROOT
    filename = uuid.uuid4().hex + '.pdf'
    full_path = os.path.join(filepath, filename)

    try:
        pdfkit.from_string(html, full_path)
    except Exception as e:
        raise ValidationError('Erro ao gerar o arquivo PDF. %s' % e.message)

    pdf = open(os.path.join(filepath, filename))

    response = HttpResponse(pdf.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=confirmation.pdf'

    pdf.close()
    os.remove('confirmation.pdf')

    return response


def render(template_src, context={}):
    try:
        template = get_template(template_src)
    except TemplateDoesNotExist:
        raise ValidationError('Template não encontrado.')

    html = template.render(context)
    
    return HttpResponse(html)


def send_mail(template_src, context={}, mail_from='', mail_to=''):
    try:
        template = get_template(template_src)
    except TemplateDoesNotExist:
        raise ValidationError('Template não encontrado.')

    html = template.render(context)

    # connect to server
    server = smtplib.SMTP(settings.SMTP, settings.SMTP_PORT)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(settings.MAIL_USER, settings.MAIL_PASS)

    # send the message
    msg = MIMEMultipart('related')
    msg['From'] = mail_from if mail_from else settings.MAIL_USER
    msg['To'] = mail_to
    msg['Subject'] = 'Confirmação de Reserva'
    msg.preamble = 'This is a multi-part message in MIME format.'

    msg_alternative = MIMEMultipart('alternative')
    msg.attach(msg_alternative)

    msg_text = MIMEText('This is the alternative plain text message.')
    msg_alternative.attach(msg_text)

    msg_text = MIMEText(html, 'html')
    msg_alternative.attach(msg_text)

    mail = server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.quit()

    return mail
