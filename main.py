import json
import telebot
import requests as req
import math
import pyowm
import random
import os
from geopy import geocoders
from dotenv import load_dotenv
load_dotenv()

# TOKENS
token_tg = os.getenv('TG_TOKEN')
token_owm = os.getenv('OWM_TOKEN')
token_accu = os.getenv('ACCU_TOKEN')
# Configs
config_dict = pyowm.utils.config.get_default_config()
config_dict['language'] = 'ru'

# init services
bot = telebot.TeleBot(token_tg)
owm = pyowm.OWM(token_owm, config_dict).weather_manager()

# default data
cityList = ["Москва","Санкт-Петербург","Новосибирск","Екатеринбург","Казань","Нижний Новгород","Челябинск","Самара","Омск","Ростов-на-Дону","Уфа","Красноярск","Воронеж","Пермь","Волгоград"]

# Определяем координаты города
def geo_pos(city: str):
    geolocator = geocoders.Nominatim(user_agent="telebot")
    latitude = str(geolocator.geocode(city).latitude)
    longitude = str(geolocator.geocode(city).longitude)
    return latitude, longitude
# Определяем кода города
def code_location(latitude: str, longitude: str, token_accu: str):
    get_url = f'http://dataservice.accuweather.com/locations/v1/cities/geoposition/search?apikey={token_accu}&q={latitude},{longitude}&language=ru'
    response = req.get(get_url, headers={'APIKey': token_accu})
    data = json.loads(response.text)
    if data['Code'] == 'ServiceUnavailable':
        code = data['Code']
        print(code)
        return code
    else:
        code = data['Key']
        return code

# ACCU - запрос погоды accuweather.com
def waetherACCU(code: str, token_accu: str):
    get_url = f'http://dataservice.accuweather.com/forecasts/v1/hourly/12hour/{code}?apikey={token_accu}&language=ru&metric=True'
    response = req.get(get_url, headers={'APIKey': token_accu})
    data = json.loads(response.text)
    accu_weather = dict()
    accu_weather['link'] = data[0]['MobileLink']
    accu_weather['сейчас'] = {'temp': data[0]['Temperature']['Value'], 'sky': data[0]['IconPhrase']}
    return accu_weather
# OWM запрос погоды openweathermap.org
def weatherOWM(city: str):
    try:
        observation = owm.weather_at_place(city)
        w = observation.weather
        status = w.detailed_status #Статус
        temp = math.floor(w.temperature('celsius')["temp"]) #Температура
        humidity = w.humidity#Влажность
        wind = math.floor(w.wind()["speed"]) #Скорость ветра

        owm_weather = "Погода в городе " + city + "\n"
        owm_weather += "Статус: " + status + "\n"
        owm_weather += "Температура: " + str(temp) + "℃" + "\n"
        owm_weather += "Влажность: " + str(humidity) + "%" + "\n"
        owm_weather += "Скорость ветра: " + str(wind) + " м/с" + "\n"
        return owm_weather
    except:
        return "Не удалось найти Ваш город попробуйте снова, а пока для Вас " + weatherOWM(random.choice(cityList))

# Messages
def accu_message(accu_weather, message):
    bot.send_message(message.from_user.id,
        f'Прогноз от accuweather.com.\n'
        f'Температура сейчас: {math.floor(accu_weather["сейчас"]["temp"])}℃'
        f' {accu_weather["сейчас"]["sky"]}'
        f' А здесь ссылка на подробности 'f'{accu_weather["link"]}')
def owm_message(owm_weather, message):
    bot.send_message(message.from_user.id, f'Прогноз от openweathermap.org\n' + owm_weather)

# Собираем данные о погоде в источниках
def get_weather(message, city):
    latitude, longitude = geo_pos(city)
    code = code_location(latitude, longitude, token_accu)
    if code != 'ServiceUnavailable':
        print("falseeeeee")
        accu_weather = waetherACCU(code, token_accu)
        accu_message(accu_weather, message)
    owm_weather = weatherOWM(city)
    owm_message(owm_weather, message)

# Приветствие при первом посещении
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, f'Я погодабот, приятно познакомитсья, {message.from_user.first_name}.'
                        f'Чтобы узнать погоду в своём городе напиши его название.'
                        f'Все мои возможность можно узнать спросив у меня командой /help')
@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message,
        f'Я могу показать тебе погоду в любом городе, для этого напиши мне его название. \n'
        f'Пока это всё что я умею.... Но я буду учиться, и потом покажу тебе что я могу')
# Отправка сообщений о погоде
@bot.message_handler(content_types=['text'])
def send_answer(message):
    if message.text.lower() == 'привет' or message.text.lower() == 'здарова':
        bot.send_message(message.from_user.id,
            f'Привет {message.from_user.first_name}, я уже говорил что умею только показывать погоду? Да вот такой вот я бот =)\n'
            f'Напиши мне название своего города')
    else:
        try:
            city = message.text.lower()
            bot.send_message(message.from_user.id, f'Одну секунду')
            get_weather(message, city)
        except AttributeError as err:
            bot.send_message(message.from_user.id,
                f'{message.from_user.first_name} я не нашел такого города,'
                f' и получил ошибку, попробуй другой город')

bot.polling(none_stop=True)
