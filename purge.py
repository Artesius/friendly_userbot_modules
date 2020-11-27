from .. import loader, utils
import logging
import telethon

logger = logging.getLogger(__name__)


@loader.tds
class PurgeMod(loader.Module):
    """Delete your messages\nRemade with love by @Art3sius"""
    strings = {"name": "Purge",
               "not_supergroup_bot": "<b>Purges can only take place in supergroups</b>",
               "delete_what": "<b>What message should be deleted?</b>"}

    @loader.sudo
    @loader.ratelimit
    async def purgecmd(self, message):
        """Purge from the replied message from [entities]\n.purge [*entities=[]]"""
        if not message.is_reply:
            await message.delete()
            return

        from_users = set()
        args = utils.get_args(message)
        for arg in args:
            try:
                entity = await message.client.get_entity(arg)
                if isinstance(entity, telethon.tl.types.User):
                    from_users.add(entity.id)
            except ValueError:
                pass

        msgs = []
        async for msg in message.client.iter_messages(
                entity=message.to_id,
                min_id=message.reply_to_msg_id - 1,
                reverse=True):
            if from_users and msg.from_id not in from_users:
                continue
            msgs.append(msg.id)
            if len(msgs) >= 99:
                await message.client.delete_messages(message.to_id, msgs)
                msgs.clear()
        if msgs:
            await message.client.delete_messages(message.to_id, msgs)

    @loader.sudo
    @loader.ratelimit
    async def delcmd(self, message):
        """Delete [n] messages after replied\n.del [n=1]"""
        msgs = [message.id]
        args = utils.get_args(message)
        count = args[0] if args != [] else 1
        async for msg in message.client.iter_messages(
                entity=message.to_id,
                limit=count,
                min_id=message.reply_to_msg_id if message.is_reply else message.id,
                reverse=True):
            msgs.append(msg.id)
            if len(msgs) >= 99:
                await message.client.delete_messages(message.to_id, msgs)
                msgs.clear()
        if msgs:
            await message.client.delete_messages(message.to_id, msgs)
