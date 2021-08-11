# requires apscheduler

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import datetime
import logging

import telethon

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class BirthdayMod(loader.Module):
    """Notifies about your friends` birthdays\nMade with love by @Art3sius"""
    strings = {
        'name': 'Birthdays',
        'person_exists': '<i>This person already exists in the database</i>',
        'person_added': '<b>Added to database</b>',
        'person_not_found': '<i>No person with this name found</i>',
        'person_deleted': '<b>Removed from database successfully</b>'
    }

    @loader.sudo
    @loader.ratelimit
    async def addbdcmd(self, message):
        """Adds a <birthday> of the <user> to the list\n.addbd <birthday> <user>"""
        args = utils.get_args(message)
        people_list = self.db.get('Birthdays', 'people_list', {})
        if ' '.join(args[1:]) in people_list:
            await utils.answer(message, self.strings('person_exists', message))
            return

        people_list[' '.join(args[1:])] = args[0]

        await self.db.set('Birthdays', 'people_list', people_list)
        await utils.answer(message, self.strings('person_added', message))

    @loader.sudo
    @loader.ratelimit
    async def delbdcmd(self, message):
        """Deletes <user> from the birthday list\n.delbd <user>"""
        args = utils.get_args(message)
        people_list = self.db.get('Birthdays', 'people_list', {})
        if ' '.join(args) not in people_list:
            await utils.answer(message, self.strings('person_not_found', message))
            return

        people_list.pop(' '.join(args))

        await self.db.set('Birthdays', 'people_list', people_list)
        await utils.answer(message, self.strings('person_deleted', message))

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        self.previous_message = None
        scheduler = AsyncIOScheduler()
        scheduler.add_job(self.checks, 'cron', hour=10)
        scheduler.start()

    async def checks(self):
        cur_time = datetime.datetime.now()
        people_list = self.db.get('Birthdays', 'people_list', {})
        today_list = list(filter(lambda x: x[1] == cur_time.strftime('%-d.%m'), people_list.items()))
        if self.previous_message:
            await self.previous_message.delete()
        self.previous_message = await self.client.send_message(
            'me', '<b>Today\'s birthdays:</b>\n\n' + '\n'.join(f'<code>{x[0]}</code>' for x in today_list)) if today_list else None
