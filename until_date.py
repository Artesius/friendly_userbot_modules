import datetime
import logging

from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class UntilDateMod(loader.Module):
    """Tells you how much time left before an event\nMade with love by @Art3sius"""
    strings = {
        'name': 'UntilDate',
        'target_time': 'Input time to wait for',
        'time_left': 'До апокаліпсису лишилось {} годин, {} хвилин і {} секунд',
        'no_time': 'Time was not set',
        'bad_time': 'Event has already passed, wtf?'
    }

    def __init__(self):
        self.config = loader.ModuleConfig("TARGET_TIME", None, lambda m: self.strings('target_time', m))

    @loader.unrestricted
    @loader.ratelimit
    async def когдаcmd(self, message):
        """Tells you how soon the scheduled event or [input_date] will happen"""
        args = utils.get_args(message)
        if not args:
            date_time = self.config['TARGET_TIME']
            if not date_time:
                await utils.answer(message, self.strings('no_time', message))
                return
        else:
            date_time = ' '.join(args)

        now = datetime.datetime.now()
        target = datetime.datetime.strptime(date_time, '%d/%m/%Y %H:%M')
        res = target - now
        if res.days < 0 or res.seconds < 0:
            await utils.answer(message, self.strings('bad_time', message))
            return
        res_string = f'{str(res.days * 24 + res.seconds // 3600)}:{str(res.seconds % 3600 // 60)}:{str(res.seconds % 60)}'
        await utils.answer(message, 'До апокаліпсису лишилось: ' + res_string)
