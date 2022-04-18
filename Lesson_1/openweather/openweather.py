import time
import requests
import os
from dotenv import load_dotenv

load_dotenv("../../.env")
API_KEY = os.getenv("OPEN_WEATHER", None)


def get_city(city: str, key: str):
    URL = f'http://api.openweathermap.org/geo/1.0/direct?q={city}&appid={key}&lang=ru'

    while True:
        time.sleep(1)
        response = requests.get(URL)
        if response.status_code == 200:
            break
    response = response.json()
    lat = response[0].get('lat')
    lon = response[0].get('lon')
    return lat, lon


def get_weather(lat: str, lon: str, key: str):
    URL = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={key}&lang=ru&units=metric'

    while True:
        time.sleep(1)
        response = requests.get(URL)
        if response.status_code == 200:
            break
    response = response.json()
    print(f'Темпрература в вашем городе - {response["name"]}, составляет - {response["main"]["temp"]} градусов.')


if __name__ == '__main__':
    print('Узнайтите погоду в любом городе.')
    city = input('Введите, название города: ')
    lat, lon = get_city(city, API_KEY)
    get_weather(lat, lon, API_KEY)
