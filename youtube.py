# requires youtube_dlc

import logging
import os
import re

import youtube_dlc
from telethon.tl.types import MessageEntityUrl

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class YoutubeMod(loader.Module):
    """Gets you an audio/video file from Youtube"""
    strings = {
        'name': 'Youtube',
        'args_error': "Can't get the link",
        'loading': 'The video is loading, please wait'
    }

    @loader.pm
    @loader.ratelimit
    async def ytdlcmd(self, message):
        """.ytdl <link>"""
        links = message.get_entities_text(MessageEntityUrl)
        if not links:
            await utils.answer(message, self.strings('args_error', message))
            return
        edit = message.out
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        }
        first = True
        for _, link in links:
            msg = await (message.edit if (edit and first) else message.respond)(self.strings('loading', message))
            with youtube_dlc.YoutubeDL(ydl_opts) as ydl:
                info_dict = await utils.run_sync(ydl.extract_info, link, download=True)
                video_id = info_dict['id']
                length = info_dict['duration']
            filename = None
            for file in os.listdir("./"):
                if file.endswith(video_id + '.mp3'):
                    filename = file[:-16]
                    filename = re.sub(r'\([^()]*\)', '', filename)
                    filename = re.sub(r'\[[^()]*\]', '', filename)
                    filename = " ".join(filename.split())
                    os.rename(file, filename + '.mp3')
            await message.respond(file=filename+'.mp3')
            await msg.delete()
