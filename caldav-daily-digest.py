#!/usr/bin/python3

"""calendar digest cron script

this logs into a caldav server and tries to get a digest of all of the
events scheduled for that day. naive and hacky but seems to mostly
work? easiest way to run this is from cron.

author: michael.o.jackson@gmail.com
modified and extended by: github@kisiel.net.pl

license: apache 2.0"""
from os import environ
from urllib.parse import quote_plus
from icalendar import Calendar
import caldav
import pytz
import sys
import datetime
import ssl
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email.utils
#import icalendar

# defaults
CAL_PROTOCOL = 'https'
LOCAL_TZ = pytz.timezone("UTC")
SMTP_SUBJECT = "Calendar - "
SMTP_PORT = 465
weird = ""
# read environment values
if "CAL_PROTOCOL" in environ:
  CAL_PROTOCOL = environ["CAL_PROTOCOL"]
if "CAL_USERNAME" in environ:
  CAL_USERNAME = environ["CAL_USERNAME"]
if "CAL_PASSWORD" in environ:
  CAL_PASSWORD = environ["CAL_PASSWORD"]
if "CAL_BASE_URL" in environ:
  CAL_BASE_URL = environ["CAL_BASE_URL"]
if "SMTP_SERVER" in environ:
  SMTP_SERVER = environ["SMTP_SERVER"]
if "SMTP_PORT" in environ:
  SMTP_PORT = environ["SMTP_PORT"]
if "SENDER_EMAIL" in environ:
  SENDER_EMAIL = environ["SENDER_EMAIL"]
if "SMTP_FROM" in environ:
  SMTP_FROM = environ["SMTP_FROM"]
if "RECEIVER_EMAIL" in environ:
  RECEIVER_EMAIL = environ["RECEIVER_EMAIL"]
if "SMTP_PASSWORD" in environ:
  SMTP_PASSWORD = environ["SMTP_PASSWORD"]
if "SMTP_SUBJECT" in environ:
  SMTP_SUBJECT = environ["SMTP_SUBJECT"]
if "TZ" in environ:
  LOCAL_TZ = pytz.timezone(environ["TZ"])

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)
URL = quote_plus(CAL_PROTOCOL) + '://' + quote_plus(CAL_USERNAME) + ":" + quote_plus(CAL_PASSWORD) \
        + '@' + CAL_BASE_URL + quote_plus(CAL_USERNAME) + '/'

NOW = datetime.datetime.now()
DAY_START = datetime.datetime(NOW.year, NOW.month, NOW.day)
DAY_END = DAY_START + datetime.timedelta(hours=24)

def pretty_print_time(date_time):
    """takes a datetime and normalizes it to local time, prints nicely"""
    local_dt = date_time.replace(tzinfo=pytz.utc).astimezone(LOCAL_TZ)
#    return local_dt.strftime("%I:%M %p")
    return local_dt.strftime("%H:%M")

def send_email(smtp_server, smtp_port, smtp_from, sender_email, receiver_email, subject, body, password):

    # Create a text message
    msg = MIMEMultipart()
    msg['From'] = email.utils.formataddr((smtp_from, sender_email))
    msg['To'] = receiver_email
    msg['Subject'] = subject

    # Attach the message body
    msg.attach(MIMEText(body, 'plain'))

    # Create a secure SSL context
    context = ssl.create_default_context()

    # Set up the SMTP server with SSL
    server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context)

    # Log in to the SMTP server
    server.login(sender_email, password)

    # Send the email
    text = msg.as_string()
    server.sendmail(sender_email, receiver_email, text)
    server.quit()

def convert_to_datetime(dt):
    if isinstance(dt, datetime.date):
        return datetime.datetime.combine(dt, datetime.time())
    else:
        return dt

CLIENT = caldav.DAVClient(URL)
PRINCIPAL = CLIENT.principal()
CALENDARS = PRINCIPAL.calendars()

# top line in email body
body = f"Agenda for {NOW.day} {NOW.strftime('%B')} {NOW.year}, {NOW.strftime('%H:%M')}\n\n"

if not CALENDARS:
# handle lack of calendars
    subject = "No calendars defined for " + CAL_USERNAME
else:
  for CALENDAR in CALENDARS:
    EVENTS = CALENDAR.date_search(DAY_START, DAY_END)

    if EVENTS:
        FILTERED_EVENTS = []
        for ev in EVENTS:
            components = Calendar.from_ical(ev.data).walk('vevent')
            if not components:
                continue
            FILTERED_EVENTS.append(components[0])
        if FILTERED_EVENTS:
          subject = "Daily Agenda for " + CAL_USERNAME
# list events from all calendars
          FILTERED_EVENTS.sort(key=lambda e: convert_to_datetime(e.decoded('dtstart').strftime('%H:%M')))
          for event in FILTERED_EVENTS:
              summary = event.decoded('summary').decode('utf-8')
              start = event.decoded('dtstart')
              end = event.decoded('dtend')

              if type(start) == datetime.date and type(end) == datetime.date:
# handle All-day events separately
                  if event.get('transp') == 'TRANSPARENT':
                    if NOW.month == start.month and NOW.day == start.day:
#I assume these ar the reccurent events that started years ago and happen say every year
                      print("transparent event")
                      body += f"All-day event: {summary}\n"
                    else:
#I don' expect them to be multiday, so I filter out the ones that did not start today
                      weird += f"All-day event: {summary}\n"
                  else:
                    body += f"All-day event: {summary}\n"
              else:
                  body += f"{pretty_print_time(start)} - {pretty_print_time(end)}: {summary}\n"
        else:
# handle empty agenda
          subject = CAL_USERNAME + " have no events scheduled today"

# add prefix to the subject for easier filtering
subject = SMTP_SUBJECT + subject

# add weird events that likely should be removed - left for testing
if weird:
  body += "\nWeird events indented to filter out\n"
  body += weird

# print for log
print(subject)
print(body)
# send email
send_email(SMTP_SERVER, SMTP_PORT, SMTP_FROM, SENDER_EMAIL, RECEIVER_EMAIL, subject, body, SMTP_PASSWORD)
