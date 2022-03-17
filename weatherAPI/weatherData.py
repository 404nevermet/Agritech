import requests

url = "https://api.openweathermap.org/data/2.5/weather"
api_key = "e83b3c4c08285bf87b99f9bbc0abe3f0"
lat = 25.774
lon = -80.1937


def get_weather_info(lat_value, lon_value):
    response = requests.get(url, params={'lat': lat_value, 'lon': lon_value, 'units': 'metric', 'appid': api_key})
    if response.status_code == 200:
        data = response.json()
        print(data)
    else:
        print("Invalid lat long")

    degree = data.get('main').get('temp')
    weather = data.get('weather')[0].get('main')
    weather_info = {'lat': lat_value, 'lon': lon_value, 'weather': weather, 'celsius': degree}
    print(weather_info)
    return weather_info


get_weather_info(lat, lon)
