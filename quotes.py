# requires: requests Pillow cryptg

import hashlib
import io
import json
import logging

import PIL
import requests
from telethon import utils
from telethon.tl.types import (
    Message, MessageEntityBold, MessageEntityItalic,
    MessageEntityMention, MessageEntityTextUrl,
    MessageEntityCode, MessageEntityMentionName,
    MessageEntityHashtag, MessageEntityCashtag,
    MessageEntityBotCommand, MessageEntityUrl,
    MessageEntityStrike, MessageEntityUnderline,
    MessageEntityPhone,
    ChatPhotoEmpty,
    MessageMediaPhoto, MessageMediaDocument, MessageMediaWebPage,
    User,
    PeerUser, PeerBlocked, PeerChannel, PeerChat,
    DocumentAttributeSticker,
    ChannelParticipantsAdmins,
    ChannelParticipantCreator
)

from .. import loader, utils as ftgUtils

logger = logging.getLogger(__name__)

PIL.Image.MAX_IMAGE_PIXELS = None


class dict(dict):
    def __setattr__(self, attr, value):
        self[attr] = value


BUILD_ID = None  # null to disable autoupdates
MODULE_PATH = "https://quotes.mishase.dev/f/module.py"


@loader.tds
class mQuotesMod(loader.Module):
    """Quote a message using Mishase Quotes API\nRemade with love by @Art3sius"""
    strings = {
        "name": "Quotes"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "QUOTE_MESSAGES_LIMIT", 5, "Messages limit",
            "MAX_WIDTH", 384, "Max width (px)",
            "SCALE_FACTOR", 5, "Scale factor",
            "SQUARE_AVATAR", False, "Square avatar",
            "TEXT_COLOR", "white", "Text color",
            "REPLY_LINE_COLOR", "white", "Reply line color",
            "REPLY_THUMB_BORDER_RADIUS", 2, "Reply thumbnail radius (px)",
            "ADMINTITLE_COLOR", "#969ba0", "Admin title color",
            "MESSAGE_BORDER_RADIUS", 10, "Message radius (px)",
            "PICTURE_BORDER_RADIUS", 8, "Picture radius (px)",
            "BACKGROUND_COLOR", "#162330", "Background color"
        )

    async def client_ready(self, client, db):
        self.client = client

    @loader.unrestricted
    @loader.ratelimit
    async def quotecmd(self, msg):
        """Quote a message. Args: ?<count> ?file"""
        args = ftgUtils.get_args_raw(msg)
        reply = await msg.get_reply_message()

        if not reply:
            return await msg.edit("No reply message")

        if not msg.out:
            msg = await msg.reply("_")

        count = 1
        force_document = False

        if args:
            args = args.split()
            force_document = "file" in args
            try:
                count = next(int(arg) for arg in args if arg.isdigit())
                count = max(1, min(self.config["QUOTE_MESSAGES_LIMIT"], count))
            except StopIteration:
                pass

        message_packer = MessagePacker(self.client)

        if count == 1:
            await msg.edit("<b>Processing...</b>")
            await message_packer.add(reply)
        if count > 1:
            it = self.client.iter_messages(
                reply.peer_id, offset_id=reply.id,
                reverse=True, add_offset=1, limit=count
            )

            i = 1
            async for message in it:
                await msg.edit(f"<b>Processing {i}/{count}</b>")
                i += 1
                await message_packer.add(message)

        messages = message_packer.messages

        if not messages:
            return await msg.edit("No messages to quote")

        files = []
        for f in message_packer.files.values():
            files.append(("files", f))

        if not files:
            files.append(("files", bytearray()))

        await msg.edit("<b>API Processing...</b>")

        resp = await ftgUtils.run_sync(
            requests.post,
            "https://quotes.mishase.dev/create",
            data={
                "data": json.dumps({
                    "messages": messages,
                    "maxWidth": self.config["MAX_WIDTH"],
                    "scaleFactor": self.config["SCALE_FACTOR"],
                    "squareAvatar": self.config["SQUARE_AVATAR"],
                    "textColor": self.config["TEXT_COLOR"],
                    "replyLineColor": self.config["REPLY_LINE_COLOR"],
                    "adminTitleColor": self.config["ADMINTITLE_COLOR"],
                    "messageBorderRadius": self.config["MESSAGE_BORDER_RADIUS"],
                    "replyThumbnailBorderRadius": self.config["REPLY_THUMB_BORDER_RADIUS"],
                    "pictureBorderRadius": self.config["PICTURE_BORDER_RADIUS"],
                    "backgroundColor": self.config["BACKGROUND_COLOR"]
                }),
                "moduleBuild": BUILD_ID
            },
            files=files,
            timeout=99
        )

        if resp.status_code == 418:
            if await update(self.allmodules.modules, msg):
                await self.allmodules.commands["quote"](msg)
            else:
                await msg.edit("<b>Update error</b>")
            return

        await msg.edit("<b>Sending...</b>")

        image = io.BytesIO()
        image.name = "quote.webp"

        PIL.Image.open(io.BytesIO(resp.content)).save(image, "WEBP")
        image.seek(0)

        await self.client.send_message(msg.peer_id, file=image, force_document=force_document)

        await msg.delete()

    @loader.unrestricted
    @loader.ratelimit
    async def fquotecmd(self, msg):
        """Fake message quote. Args: @<username>/<id>/<reply> <text>"""
        args = ftgUtils.get_args_raw(msg)
        reply = await msg.get_reply_message()
        split_args = args.split(maxsplit=1)
        if len(split_args) == 2 and (split_args[0].startswith("@") or split_args[0].isdigit()):
            user = split_args[0][1:] if split_args[0].startswith(
                "@") else int(split_args[0])
            text = split_args[1]
        elif reply:
            user = reply.sender_id
            text = args
        else:
            return await msg.edit("Incorrect args")

        try:
            uid = (await self.client.get_entity(user)).id
        except Exception:
            return await msg.edit("User not found")

        async def get_message():
            return Message(0, uid, message=text)

        msg.message = ""
        msg.get_reply_message = get_message

        await self.quotecmd(msg)


class MessagePacker:
    def __init__(self, client):
        self.files = dict()
        self.messages = []
        self.client = client

    async def add(self, msg):
        packed = await self.pack_message(msg)
        if packed:
            self.messages.append(packed)

    async def pack_message(self, msg):
        obj = dict()

        text = msg.message
        if text:
            obj.text = text

        entities = MessagePacker.encode_entities(msg.entities or [])
        if entities:
            obj.entities = entities

        media = msg.media
        if media:
            file = await self.download_media(media)
            if file:
                obj.picture = {
                    "file": file
                }

        if "text" not in obj and "picture" not in obj:
            return

        obj.author = await self.encode_author(msg)

        reply = await msg.get_reply_message()
        if reply:
            obj.reply = await self.encode_reply(reply)

        return obj

    @staticmethod
    def encode_entities(entities):
        enc_entities = []
        for entity in entities:
            entity_type = MessagePacker.get_entity_type(entity)
            if entity_type:
                enc_entities.append({
                    "type": entity_type,
                    "offset": entity.offset,
                    "length": entity.length
                })
        return enc_entities

    @staticmethod
    def get_entity_type(entity):
        t = type(entity)
        if t is MessageEntityBold:
            return "bold"
        if t is MessageEntityItalic:
            return "italic"
        if t in [MessageEntityUrl, MessageEntityPhone]:
            return "url"
        if t is MessageEntityCode:
            return "monospace"
        if t is MessageEntityStrike:
            return "strikethrough"
        if t is MessageEntityUnderline:
            return "underline"
        if t in [MessageEntityMention, MessageEntityTextUrl, MessageEntityMentionName,
                 MessageEntityHashtag, MessageEntityCashtag, MessageEntityBotCommand]:
            return "bluetext"
        return

    async def download_media(self, in_media, thumb=None):
        media = MessagePacker.get_media(in_media)
        if not media:
            return
        mid = str(media.id)
        if thumb:
            mid += "." + str(thumb)
        if mid not in self.files:
            try:
                mime = media.mime_type
            except AttributeError:
                mime = "image/jpg"
            dl = await self.client.download_media(media, bytes, thumb=thumb)
            self.files[mid] = (str(len(self.files)), dl, mime)
        return self.files[mid][0]

    @staticmethod
    def get_media(media):
        t = type(media)
        if t is MessageMediaPhoto:
            return media.photo
        if t is MessageMediaDocument:
            for attribute in media.document.attributes:
                if isinstance(attribute, DocumentAttributeSticker):
                    return media.document
        elif t is MessageMediaWebPage:
            if media.webpage.type == "photo":
                return media.webpage.photo
        return

    async def download_profile_picture(self, entity):
        media = entity.photo
        if not media or isinstance(media, ChatPhotoEmpty):
            return
        mid = str(media.photo_id)
        if mid not in self.files:
            dl = await self.client.download_profile_photo(entity, bytes)
            self.files[mid] = (str(len(self.files)), dl, "image/jpg")
        return self.files[mid][0]

    async def encode_author(self, msg):
        obj = dict()

        uid, name, picture, admin_title = await self.get_author(msg)

        obj.id = uid
        obj.name = name
        if picture:
            obj.picture = {
                "file": picture
            }
        if admin_title:
            obj.adminTitle = admin_title

        return obj

    async def get_author(self, msg, full=True):
        uid = None
        name = None
        picture = None
        admin_title = None

        chat = msg.peer_id
        peer = msg.from_id or chat
        fwd = msg.fwd_from
        if fwd:
            peer = fwd.from_id
            name = fwd.post_author or fwd.from_name

        t = type(peer)
        if t is int:
            uid = peer
        elif t is PeerUser:
            uid = peer.user_id
        elif t is PeerChannel:
            uid = peer.channel_id
        elif t is PeerChat:
            uid = peer.chat_id
        elif t is PeerBlocked:
            uid = peer.peer_id
        elif not peer:
            uid = int(hashlib.shake_256(
                name.encode("utf-8")).hexdigest(6), 16)

        if not name:
            try:
                entity = await self.client.get_entity(peer)
            except Exception:
                entity = await msg.get_chat()

            if isinstance(entity, User) and entity.deleted:
                name = "Deleted Account"
            else:
                name = utils.get_display_name(entity)

            if full:
                picture = await self.download_profile_picture(entity)

                if isinstance(chat, PeerChannel):
                    admins = await self.client.get_participants(chat, filter=ChannelParticipantsAdmins)
                    for admin in admins:
                        participant = admin.participant
                        if participant.user_id == uid:
                            admin_title = participant.rank
                            if not admin_title:
                                if isinstance(participant, ChannelParticipantCreator):
                                    admin_title = "owner"
                                else:
                                    admin_title = "admin"
                            break

        return uid, name, picture, admin_title

    async def encode_reply(self, reply):
        obj = dict()

        text = reply.message
        if text:
            obj.text = text
        else:
            media = reply.media
            if media:
                t = type(media)
                if t is MessageMediaPhoto:
                    obj.text = "📷 Photo"
                else:
                    obj.text = "💾 File"

        name = (await self.get_author(reply, full=False))[1]

        obj.author = name

        media = reply.media
        if media:
            file = await self.download_media(media, -1)
            if file:
                obj.thumbnail = {
                    "file": file
                }

        return obj


async def update(modules, message, url=MODULE_PATH):
    loader = next(filter(lambda x: "LoaderMod" ==
                                   x.__class__.__name__, modules))
    try:
        if await loader.download_and_install(url, message):
            loader._db.set(__name__, "loaded_modules",
                           list(set(loader._db.get(__name__, "loaded_modules", [])).union([url])))
            return True
        else:
            return False
    except Exception:
        return False
