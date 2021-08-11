# requires pillow, opencv_python_headless, ffmpeg_python, moviepy

import io
import logging
import os
import requests
import uuid
from random import choice
from textwrap import fill

import cv2
import ffmpeg
from moviepy.editor import VideoFileClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageOps, ImageFont

from .. import loader, utils


logger = logging.getLogger(__name__)


@loader.tds
class DemotivatorMod(loader.Module):
    """Demotivators creating\nRemade with love by @Art3sius"""
    strings = {
        'name': 'Demotivator',
        'incorrect_filetype': '<i>Incorrect_filetype</i>',
        'process_started': '<b>Demotivating...</b>'
    }

    @loader.pm
    @loader.ratelimit
    async def demoticmd(self, message):
        """Add a demotivator under your file"""
        await self.cmds(message, 0)

    @loader.pm
    @loader.ratelimit
    async def demotcmd(self, message):
        """Resize an image and add a demotivator"""
        await self.cmds(message, 1)

    async def cmds(self, message, mode):
        msg = message
        if not msg.file:
            msg = await msg.get_reply_message()

        if msg.file.mime_type.split("/")[0].lower() not in ['image', 'video']:
            await utils.answer(message, self.strings('incorrect_filetype', message))
            return

        text = utils.get_args_raw(message)
        if not text:
            text = choice(standart_response)

        edit = message.out
        mess = await (message.edit if edit else message.respond)(self.strings('process_started', message))
        if msg.file.mime_type.split("/")[0].lower() == 'image':
            bytes_file = await msg.download_media(bytes)
            demotivator = demote_image(bytes_file, mode, text)
        else:
            filename = str(uuid.uuid4().hex) + '.mp4'
            with open(filename, 'wb') as file:
                await msg.download_media(file)
            demotivator = demote_video(filename, text)

        await msg.reply(file=demotivator)
        await mess.delete()
        os.remove(demotivator)

    async def client_ready(self, client, db):
        self.client = client


def draw_main(bytes_image, mode):
    photo = Image.open(io.BytesIO(bytes_image))
    image = Image.new("RGB", photo.size, 'black')
    image.paste(photo, (0, 0))
    image = image.resize((700, 550)) if mode else image
    image = ImageOps.expand(image, 5, 'black')
    image = ImageOps.expand(image, 3, 'white')
    width, height = image.size
    border = height // 8
    result = Image.new("RGB", (width + 2 * border, height + border), 'black')
    result.paste(image, (border, border))
    return result


def draw_text(text, main, size):
    font = ImageFont.truetype(io.BytesIO(font_file), size)
    width, height = ImageDraw.Draw(Image.new("RGB", (1, 1))).multiline_textsize(text=text, font=font)
    image = Image.new("RGB", (width, height + 30), 'black')
    ImageDraw.Draw(image).text((0, 0), text=text, font=font, fill='white', align='center')
    border_width = width // 4
    border_height = (height + 30) // 4
    text_img = Image.new("RGB", (width + 2 * border_width, (height + 30) + 2 * border_height), 'black')
    text_img.paste(image, (border_width, border_height))
    x = min(main.size)
    text_img.thumbnail((x, x))
    return text_img


def merge(image, text):
    image_width, image_height = image.size
    text_width, text_height = text.size
    result = image.crop((0, 0, image_width, image_height + text_height))
    result.paste(text, ((image_width - text_width) // 2, image_height))
    return result


def demote_image(image, mode, text):
    image = draw_main(image, mode)
    text_image = draw_text(fill(text), image, min(image.size) // 5)
    output = merge(image, text_image)
    filename = str(uuid.uuid4().hex) + '.jpg'
    output.save(filename)
    return filename


def demote_video(video, text):
    vid = cv2.VideoCapture(video)
    last_frame = None
    success, frame = vid.read()
    while success:
        last_frame = frame
        success, frame = vid.read()
    filename = str(uuid.uuid4().hex) + '.jpg'
    cv2.imwrite(filename, last_frame)
    image = draw_main(filename, 0)
    text_image = draw_text('\n'.join([fill(line) for line in text.split('\n')]), image, min(image.size) // 5)
    output = merge(image, text_image)
    source = Image.open(filename)
    output = output.resize(source.size)
    source.close()
    filename2 = str(uuid.uuid4().hex) + '.jpg'
    output.save(filename2)

    filename3 = str(uuid.uuid4().hex) + '.mp4'
    img = ffmpeg.input(filename2)
    if not os.path.isfile('audio.mp3'):
        with open('audio.mp3', 'wb') as file:
            file.write(audio_file)
    audio = ffmpeg.input('audio.mp3')
    (
        ffmpeg
        .concat(img, audio, v=1, a=1)
        .output(filename3)
        .run(overwrite_output=True)
    )

    video1 = VideoFileClip(video)
    video2 = VideoFileClip(filename3)

    final_video = concatenate_videoclips([video1, video2])
    filename4 = str(uuid.uuid4().hex) + '.mp4'
    final_video.write_videofile(filename4)
    os.remove(filename)
    os.remove(filename2)
    os.remove(filename3)
    return filename4


standart_response = ['А че', 'заставляет задуматься', 'Жалко пацана', 'ты че сука??', 'ААХАХАХАХХАХА\n\nААХАХААХАХА',
                     'ГИГАНТ МЫСЛИ\n\nотец русской демократии', 'Он', 'ЧТО БЛЯТЬ?', 'охуенная тема',
                     'ВОТ ОНИ\n\nтипичные комедиклабовские шутки', 'НУ НЕ БЛЯДИНА?', 'Узнали?', 'Согласны?',
                     'Вот это мужик', 'ЕГО ИДЕИ\n\nбудут актуальны всегда', '\n\nПРИ СТАЛИНЕ ОН БЫ СИДЕЛ', 'о вадим',
                     '2 месяца на дваче\n\nи это, блядь, нихуя не смешно', 'Что дальше?\n\nЧайник с функцией жопа?',
                     '\n\nИ нахуя мне эта информация?', 'Верхний текст', 'нижний текст', 'Показалось',
                     'Суды при анкапе', 'Хуйло с района\n\n\n\nтакая шелупонь с одной тычки ляжет', 'Брух',
                     'Расскажи им\n\nкак ты устал в офисе', 'Окурок блять\n\nесть 2 рубля?', 'Аниме ставшее легендой',
                     'СМИРИСЬ\n\n\n\nты никогда не станешь настолько же крутым', 'а ведь это идея',
                     '\n\nЕсли не лайкнешь у тебя нет сердца', 'Вместо тысячи слов', 'ШАХ И МАТ!!!',
                     'Самый большой член в мире\n\nУ этой девушки', 'Немного\n\nперфекционизма', 'кто',
                     '\n\nэта сука уводит чужих мужей', 'Кто он???', '\n\nВы тоже хотели насрать туда в детстве?',
                     '\n\nВся суть современного общества\n\nв одном фото', 'Он обязательно выживет!',
                     '\n\nВы тоже хотите подрочить ему?', '\n\nИ вот этой хуйне поклоняются русские?',
                     'Вот она суть\n\n\n\nчеловеческого общества в одной картинке',
                     'Вы думали это рофл?\n\nНет это жопа',
                     '\n\nПри сталине такой хуйни не было\n\nА у вас было?', 'Он грыз провода',
                     'Назло старухам\n\nна радость онанистам', 'Где-то в Челябинске', 'Агитация за Порошенко',
                     'ИДЕАЛЬНО', 'Грыз?',
                     'Ну давай расскажи им\n\nкакая у тебя тяжелая работа', '\n\nЖелаю в каждом доме такого гостя',
                     'Шкура на вырост', 'НИКОГДА\n\nне сдавайся', 'Оппа гангнам стайл\n\nуууу сэкси лейди оп оп',
                     'Они сделали это\n\nсукины дети, они справились', 'Эта сука\n\nхочет денег', 'Это говно, а ты?',
                     '\n\nВот она нынешняя молодежь', 'Погладь кота\n\nпогладь кота сука', 'Я обязательно выживу',
                     '\n\nВот она, настоящая мужская дружба\n\nбез политики и лицимерия',
                     '\n\nОБИДНО ЧТО Я ЖИВУ В СТРАНЕ\n\nгде гантели стоят в 20 раз дороже чем бутылка водки',
                     'Царь, просто царь',
                     '\n\nНахуй вы это в учебники вставили?\n\nИ ещё ебаную контрольную устроили',
                     '\n\nЭТО НАСТОЯЩАЯ КРАСОТА\n\nа не ваши голые бляди', '\n\nТема раскрыта ПОЛНОСТЬЮ',
                     '\n\nРОССИЯ, КОТОРУЮ МЫ ПОТЕРЯЛИ', 'ЭТО - Я\n\nПОДУМАЙ МОЖЕТ ЭТО ТЫ', 'почему\n\nчто почему',
                     'КУПИТЬ БЫ ДЖЫП\n\nБЛЯТЬ ДА НАХУЙ НАДО', '\n\n\n\nмы не продаём бомбастер лицам старше 12 лет',
                     'МРАЗЬ',
                     'Правильная аэрография', 'Вот она русская\n\nСМЕКАЛОЧКА', 'Он взял рехстаг!\n\nА чего добился ты?',
                     'На аватарку', 'Фотошоп по-деревенски', 'Инструкция в самолете', 'Цирк дю Солей',
                     'Вкус детства\n\nшколоте не понять', 'Вот оно - СЧАСТЬЕ',
                     'Он за тебя воевал\n\nа ты даже не знаешь его имени', 'Зато не за компьютером',
                     '\n\nНе трогай это на новый год', 'Мой первый рисунок\n\nмочой на снегу',
                     '\n\nМайские праздники на даче',
                     'Ваш пиздюк?', 'Тест драйв подгузников', 'Не понимаю\n\nкак это вообще выросло?',
                     'Супермен в СССР',
                     'Единственный\n\nкто тебе рад', 'Макдональдс отдыхает', 'Ну че\n\n как дела на работе пацаны?',
                     'Вся суть отношений', 'Беларусы, спасибо!', '\n\nУ дверей узбекского военкомата',
                     'Вместо 1000 слов',
                     'Один вопрос\n\nнахуя?', 'Ответ на санкции\n\nЕВРОПЫ', 'ЦЫГАНСКИЕ ФОКУСЫ',
                     'Блять!\n\nда он гений!',
                     '\n\nУкраина ищет новые источники газа', 'ВОТ ЭТО\n\nНАСТОЯЩИЕ КАЗАКИ а не ряженные',
                     'Нового года не будет\n\nСанта принял Ислам',
                     '\n\nОн был против наркотиков\n\nа ты и дальше убивай себя',
                     'Всем похуй!\n\nВсем похуй!', 'БРАТЬЯ СЛАВЯНЕ\n\nпомните друг о друге',
                     '\n\nОН ПРИДУМАЛ ГОВНО\n\nа ты даже не знаешь его имени', '\n\nкраткий курс истории нацболов',
                     'Эпоха ренессанса']
font_file = requests.get("https://raw.githubusercontent.com/KeyZenD/l/master/times.ttf").content
audio_file = requests.get('https://raw.githubusercontent.com/Artesius/friendly_userbot_modules/main/demotivator_files/audio.mp3').content
