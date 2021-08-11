import logging

import telethon
from telethon.tl.types import Message

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class BoldMessageMod(loader.Module):
    """Make your messages bold\nMade with love by @Art3sius"""
    strings = {
        'name': 'ArtBold',
        'chat_list': 'List of chat ids to bold'
    }

    def __init__(self):
        self.config = loader.ModuleConfig("CHAT_LIST", None, lambda m: self.strings('chat_list', m))

    def config_complete(self):
        if self.config['CHAT_LIST']:
            if type(self.config['CHAT_LIST']) == str:
                self.chats = list(map(int, self.config['CHAT_LIST'].split()))
            else:
                self.chats = [self.config['CHAT_LIST']]
        else:
            self.chats = None

    async def watcher(self, message):
        if not isinstance(message, Message) or not self.chats:
            return

        if message.out and message.message:
            if message.chat and message.chat.id in self.chats:
                await utils.answer(message, f'<b>{message.text}</b>')
