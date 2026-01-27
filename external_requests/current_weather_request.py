import requests
from .request_api_abstract import RequestApi
from typing import Any, Dict

class CurrentWeatherRequest(RequestApi):
    
    def get_response(self) -> Dict[str, Any] | None:
        self.__BASE_URL: str = "http://api.weatherapi.com/v1/current.json" #base url
        self.__FILE: Any = open("./src/tokens.txt", "r") #open file in read mode
        self.__token: str = self.__FILE.readlines()[-1] #read token from that file
        self.__FILE.close() #close the file
        #getting weather data for that given latitude and longitude:
        self.__response: requests.Response = requests.get(self.__BASE_URL, params = {'key': self.__token, 'q': str(self.latitude) + ',' + str(self.longitude)})
        if self.__response.status_code == 200:
            return self.__response.json()
        else:
            raise requests.HTTPError(f"Something went wrong with the request to the WeatherAPI. Status: {self.__response.status_code}")

if __name__ == '__main__':
    weather = CurrentWeatherRequest(2.5200, 11.4050)
    print(weather.get_response())