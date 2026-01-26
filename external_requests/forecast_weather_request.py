import requests
from typing import Dict, Any
from .request_api_abstract import RequestApi

class ForecastWeatherRequest(RequestApi):
    
    def get_response(self) -> Dict[str, Any] | None:

        self.__BASE_URL: str = "http://api.weatherapi.com/v1/forecast.json"
        self.__FILE: Any = open("./src/tokens.txt")
        self.__token: str = self.__FILE.readlines()[-1]
        self.__FILE.close()
        self.__response: requests.Response = requests.get(
                                    self.__BASE_URL,
                                    params = {"key" : self.__token, "q": str(self.latitude) + "," + str(self.longitude), "days" : 7}
                                    )
        if self.__response.status_code == 200:
            return self.__response.json()
        else:
            raise requests.HTTPError(f"Something went wrong with the request to the WeatherAPI\nStatus: {self.__response.status_code}")

if __name__ == "__main__":
    forecast = ForecastWeatherRequest(48.8567, 2.3508)
    from pprint import pprint
    pprint(forecast.get_response())