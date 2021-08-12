# requires apscheduler, google-api-python-client, google-auth, google-auth-oauthlib, google-auth-httplib2

import datetime
import logging

import googleapiclient.discovery
import telethon
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from google.oauth2 import service_account

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class BirthdayMod(loader.Module):
    """Notifies about your friends` birthdays\nSynchronizes with Google Calendar\nMade with love by @Art3sius"""
    strings = {
        'name': 'Birthdays',
        'calendar_id': 'Id of Google calendar to store birthdays',
        'service_file': 'Name of the service account json',
        'person_exists': '<i>This person already exists in the database</i>',
        'person_added': '<b>Added to database</b>',
        'person_not_found': '<i>No person with this name found</i>',
        'person_deleted': '<b>Removed from database successfully</b>'
    }

    def __init__(self):
        self.config = loader.ModuleConfig("CALENDAR_ID", None, lambda m: self.strings('calendar_id', m),
                                          "SERVICE_FILE", None, lambda m: self.strings('service_file', m))

    @loader.sudo
    @loader.ratelimit
    async def addbdcmd(self, message):
        """Adds a <birthday> of the <user> to the list\n.addbd <birthday> <user>"""
        args = utils.get_args(message)
        people_list = self.db.get('Birthdays', 'people_list', {})
        if ' '.join(args[1:]) in people_list:
            await utils.answer(message, self.strings('person_exists', message))
            return

        result = [args[0]]

        if self.sync:
            birth_date = datetime.datetime.strptime(args[0], '%d.%m')
            today = datetime.date.today()
            result_date = datetime.datetime(today.year, birth_date.month, birth_date.day)
            start = (result_date + datetime.timedelta(hours=10)).isoformat()
            end = (result_date + datetime.timedelta(hours=19)).isoformat()
            event = {
                'summary': 'Birthday of ' + ' '.join(args[1:]),
                'description': 'Happy birthday! Created with Art3sius-Telegram',
                'start': {
                    'dateTime': start,
                    'timeZone': 'Europe/Helsinki'
                },
                'end': {
                    'dateTime': end,
                    'timeZone': 'Europe/Helsinki'
                },
                'recurrence': [
                    'RRULE:FREQ=YEARLY'
                ]
            }
            new_event = self.service.events().insert(calendarId=self.config['CALENDAR_ID'], body=event).execute()
            result.append(new_event['id'])

        people_list[' '.join(args[1:])] = result

        await self.db.set('Birthdays', 'people_list', people_list)
        await utils.answer(message, self.strings('person_added', message))

    @loader.sudo
    @loader.ratelimit
    async def delbdcmd(self, message):
        """Deletes <user> from the birthday list\n.delbd <user>"""
        args = utils.get_args(message)
        name = ' '.join(args)
        people_list = self.db.get('Birthdays', 'people_list', {})
        if name not in people_list:
            await utils.answer(message, self.strings('person_not_found', message))
            return

        if len(people_list[name]) > 1:
            self.service.events().delete(calendarId=self.config['CALENDAR_ID'],
                                         eventId=people_list[name][1],
                                         sendNotifications=False).execute()
        people_list.pop(name)

        await self.db.set('Birthdays', 'people_list', people_list)
        await utils.answer(message, self.strings('person_deleted', message))

    def config_complete(self):
        self.sync = self.config['CALENDAR_ID'] and self.config['SERVICE_FILE']

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        self.previous_message = None
        if not self.sync:
            scheduler = AsyncIOScheduler()
            scheduler.add_job(self.checks, 'cron', hour=10)
            scheduler.start()
        else:
            scopes = ['https://www.googleapis.com/auth/calendar']
            service_account_file = self.config['SERVICE_FILE']

            credentials = service_account.Credentials.from_service_account_file(service_account_file, scopes=scopes)
            self.service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)

    async def checks(self):
        cur_time = datetime.datetime.now()
        people_list = self.db.get('Birthdays', 'people_list', {})
        today_list = list(filter(lambda x: x[1][0] == cur_time.strftime('%-d.%m'), people_list.items()))
        if self.previous_message:
            await self.previous_message.delete()
        self.previous_message = await self.client.send_message(
            'me', '<b>Today\'s birthdays:</b>\n\n' +
                  '\n'.join(f'<code>{x[0]}</code>' for x in today_list)) if today_list else None
