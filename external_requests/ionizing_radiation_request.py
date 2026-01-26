from typing import Dict, Any, List
import requests
from .request_api_abstract import RequestApi

class IonizingRadiationRequest(RequestApi):

    def __init__(self, latitude: float | int, longitude: float | int, radius: float | int):
        super().__init__(latitude = latitude, longitude = longitude)
        #Raises error if raidus is not numeric.
        if not isinstance(radius, (int, float)):
            raise TypeError('The arguments can either be float or int, nothing else') 
        
        self.__radius: int | float = radius
        
    def get_response(self) -> List[Dict[str, Any]] | None:
        self.__FILE: Any = open("./src/tokens.txt", "r")
        self.__token: str = self.__FILE.readlines()[1][:-1]
        self.__FILE.close()
        self.__BASE_URL: str = "https://api.safecast.org/measurements.json"
        self.__response: requests.Response = requests.get(
                                                self.__BASE_URL,
                                                headers = {"X-API-KEY" : self.__token},
                                                params = {
                                                    "latitude" : self.latitude,
                                                    "longitude" : self.longitude,
                                                    "distance" : self.__radius
                                                        }
                                            )
        if self.__response.status_code == 200:
            return self.__response.json()
        else:
            #Note: HTTPError occurs when the request has a bad status code (4xx for client side issues, 5xx for server side issues)
            raise requests.HTTPError(f"Something went wrong during a request to safecastAPI\nStatus: {self.__response.status_code}")

if __name__ == "__main__":
    radiation = IonizingRadiationRequest(48.8575, 2.3514, 20)
    from pprint import pprint
    pprint(radiation.get_response())