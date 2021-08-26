# requires apscheduler

import datetime
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class UntilDateMod(loader.Module):
    """Tells you how much time left before an event\nMade with love by @Art3sius"""
    strings = {
        'name': 'UntilDate'
    }

    async def client_ready(self, client, db):
        self.client = client

        scheduler = AsyncIOScheduler()
        scheduler.add_job(self.checks, 'interval', seconds=1)
        scheduler.start()

    async def checks(self):
        now = datetime.datetime.now()
        target = datetime.datetime(2021, 8, 31, 14)
        res = target - now
        if res.days < 0 or res.seconds < 0:
            return
        res_string = f'{str(res.days * 24 + res.seconds // 3600)}:{str(res.seconds % 3600 // 60)}:{str(res.seconds % 60)}'
        try:
            await self.client.edit_message(1588152056, 33404, '<i>До апокаліпсису лишилось: ' + res_string + '</i>')
        except:
            pass