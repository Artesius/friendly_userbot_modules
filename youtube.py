# requires youtube_dlc

import logging
import os
import re

import youtube_dlc
from telethon.tl.types import DocumentAttributeAudio, MessageEntityUrl

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class YoutubeMod(loader.Module):
    """Get you an audio/video file from Youtube\nMade with love by @Art3sius"""
    strings = {
        'name': 'Youtube',
        'args_error': "<i>Can't get the link</i>",
        'loading': '<b>The video is loading, please wait</b>'
    }

    @loader.pm
    @loader.ratelimit
    async def ytdlcmd(self, message):
        """Download an <audio> from Youtube\n.ytdl <link>"""
        links = message.get_entities_text(MessageEntityUrl)
        if not links:
            await utils.answer(message, self.strings('args_error', message))
            return
        ydl_opts = {
            'cachedir': False,
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        }
        edit = message.out
        first = True
        for _, link in links:
            msg = await (message.edit if (edit and first) else message.respond)(self.strings('loading', message))
            first = False
            with youtube_dlc.YoutubeDL(ydl_opts) as ydl:
                info_dict = await utils.run_sync(ydl.extract_info, link, download=True)
                video_id = info_dict['id']
                length = info_dict['duration']
            filename = None
            for file in os.listdir("./"):
                if file.endswith(video_id + '.mp3'):
                    filename = file[:-16]
                    filename = re.sub(r'\([^()]*\)', '', filename)
                    filename = re.sub(r'\[[^()]*]', '', filename)
                    filename = " ".join(filename.split())
                    os.rename(file, filename + '.mp3')
            splitter = max([filename.find(text) for text in [' - ', ' – ', ' — ']])
            if splitter > -1:
                attrs = DocumentAttributeAudio(length, title=filename[splitter+3:], performer=filename[:splitter])
            else:
                attrs = DocumentAttributeAudio(length, title=filename, performer='Art3sius')
            await self.client.send_file(entity=message.chat, file=filename+'.mp3', attributes=[attrs])
            await msg.delete()
            os.remove(filename+'.mp3')

    async def client_ready(self, client, db):
        self.client = client
