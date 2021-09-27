# requires: pyowm

import logging
import pyowm
import math

from .. import loader, utils

from ..utils import escape_html as eh

logger = logging.getLogger(__name__)


def deg_to_text(deg):
    if deg is None:
        return None
    return ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW",
            "SW", "WSW", "W", "WNW", "NW", "NNW"][round(deg / 22.5) % 16]


def round_to_sf(n, digits):
    return round(n, digits - 1 - int(math.floor(math.log10(abs(n)))))


@loader.tds
class WeatherMod(loader.Module):
    """Checks the weather\nRemade with love by @Art3sius"""
    strings = {"name": "Weather",
               "provide_api": "<b>Please provide an API key via the configuration mode.</b>",
               "invalid_temp_units": "<b>Invalid temperature units provided. Please reconfigure the module.</b>",
               "doc_default_loc": "OpenWeatherMap City ID",
               "doc_api_key": "API Key from https://openweathermap.org/appid",
               "doc_temp_units": "Temperature unit as English",
               "result": "<i>Weather in {loc} is {w} with a temperature between {low} and {high}, "
                         "averaging at {avg}°C with {humid}% humidity and a {ws} meters per second {wd} wind.</i>",
               "unknown": "unknown"}

    def __init__(self):
        self.config = loader.ModuleConfig("DEFAULT_LOCATION", None, lambda m: self.strings("doc_default_loc", m),
                                          "API_KEY", None, lambda m: self.strings("doc_api_key", m),
                                          "TEMP_UNITS", "celsius", lambda m: self.strings("doc_temp_units", m))
        self._owm = None

    def config_complete(self):
        if self.config["API_KEY"]:
            self._owm = pyowm.OWM(self.config["API_KEY"]).weather_manager()
        else:
            self._owm = None

    @loader.unrestricted
    @loader.ratelimit
    async def weathercmd(self, message):
        """.weather [location]"""
        if self._owm is None:
            await utils.answer(message, self.strings("provide_api", message))
            return
        args = utils.get_args_raw(message)
        func = None
        if not args:
            func = self._owm.weather_at_id
            args = [self.config["DEFAULT_LOCATION"]]
        else:
            try:
                args = [int(args)]
                func = self._owm.weather_at_id
            except ValueError:
                coords = utils.get_args_split_by(message, ",")
                if len(coords) == 2:
                    try:
                        args = [int(coord.strip()) for coord in coords]
                        func = self._owm.weather_at_coords
                    except ValueError:
                        pass
        if func is None:
            func = self._owm.weather_at_place
            args = [args]
        logger.debug(func)
        logger.debug(args)
        observation = await utils.run_sync(func, *args)
        logger.debug("Weather at %r is %r", args, observation)
        try:
            weather = observation.weather
            temperature = weather.temperature(self.config["TEMP_UNITS"])
        except ValueError:
            await utils.answer(message, self.strings("invalid_temp_units", message))
            return
        ret = self.strings("result", message).format(loc=eh(observation.location.name),
                                                     w=eh(weather.detailed_status.lower()),
                                                     high=eh(temperature["temp_max"]), low=eh(temperature["temp_min"]),
                                                     avg=eh(temperature["temp"]), humid=eh(weather.humidity),
                                                     ws=eh(round_to_sf(weather.wind()["speed"], 3)),
                                                     wd=eh(deg_to_text(weather.wind().get("deg", None))
                                                           or self.strings("unknown", message)))
        await utils.answer(message, ret)
