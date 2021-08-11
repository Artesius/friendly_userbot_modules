# requires lyrics_extractor, transliterate

import logging

from .. import loader, utils

from lyrics_extractor import SongLyrics, lyrics
from transliterate import translit, exceptions

logger = logging.getLogger(__name__)


@loader.tds
class LyricsMod(loader.Module):
    """Finds lyrics for selected song\nMade with love by @Art3sius"""
    strings = {
        'name': 'Lyrics',
        'docstring_API': 'Google Search Engine API',
        'docstring_Hash': 'Google Search Engine Hash',
        'missing_token': '<i>API or hash tokens are missing</i>',
        'args_error': "<i>You didn't specify the song</i>",
        'not_found': '<i>Invalid song</i>'
    }

    def __init__(self):
        self.config = loader.ModuleConfig("Lyrics_API", None, lambda m: self.strings('docstring_API', m),
                                          "Lyrics_Hash", None, lambda m: self.strings('docstring_Hash', m))

    def config_complete(self):
        if self.config['Lyrics_API'] and self.config['Lyrics_Hash']:
            self.engine = SongLyrics(self.config['Lyrics_API'], self.config['Lyrics_Hash'])
        else:
            self.engine = None

    @loader.pm
    @loader.ratelimit
    async def lyricscmd(self, message):
        """Search for lyrics on a <song>\n.lyrics <song>"""
        if self.engine is None:
            await utils.answer(message, self.strings('missing_token', message))
            return
        name = utils.get_args_raw(message)
        if name == '':
            await utils.answer(message, self.strings('args_error', message))
            return
        try:
            request = translit(name, reversed=True)
        except exceptions.LanguageDetectionError:
            request = name
        try:
            info = self.engine.get_lyrics(request)
        except lyrics.LyricScraperException:
            await utils.answer(message, self.strings('not_found', message))
            return
        await utils.answer(message, info['lyrics'], asfile=True, filename=f"{info['title']}.txt")

