from flask import request
from flask_restful import reqparse, Resource, abort, Api
from typing import Dict, Tuple, Any, List
from abc import ABC, abstractmethod
from external_requests import CurrentWeatherRequest, IonizingRadiationRequest
from data_handling import DataHandler
import requests
import math

class HTTP:

    class ForceGET(ABC):

        @abstractmethod
        def get(self) -> Tuple[Dict[str, Any], int]: #Forcing a polymorphism over the GET HTTP method.
            pass

    class Util:

        def auth(self, has_detail: bool) -> None:

            if has_detail:
                #Validating the presence of value.
                if self.latitude is None or self.longitude is None or self.detail is None:
                    abort(400, message = "Invalid request. You must define a value for latitude, longitude and detail parameters.")
                #Validating if detail has correct value.
                if self.detail in ("true", "True"):
                    self.detail_bool: bool = True
                elif self.detail in ("False", "false"):
                    self.detail_bool: bool = False
                else:
                    #This case should have a response with 400 (bad request) as status code.
                    abort(400, message = "Invalid request for detail parameter. You must provide either True or False, nothing else!")
            else:
                if self.latitude is None or self.longitude is None: #Validating the presence of value.
                    abort(400, message = "Invalid request. You must define a value for latitude and longitude parameters.")
            
            if self.latitude < -90 or self.latitude > 90: #Validating the range of latitude.
                abort(400, message = "Invalid value for latitude! It ranges from -90 deg to 90 deg")
            
            if self.longitude < -180 or self.longitude > 180: #Validating the range of longitude.
                abort(400, message = "Invalid value for longitude! It must range from -180 deg to 180 deg")

    class EnvironmentDataNow(ForceGET, Util, Resource):

        def get(self) -> Tuple[Dict[str, Any], int]:
            self.__std_radius: int = 10 #The standard radius to search for ionizing radiation measurement is 10km
            self.latitude: float = request.args.get("latitude", type = float)
            self.longitude: float = request.args.get("longitude", type = float)
            self.detail: str = request.args.get("detail")
            
            self.auth(True) #Authenticating data given by the user and creating the self.detail_bool
            
            self.__weather: CurrentWeatherRequest = CurrentWeatherRequest(latitude=self.latitude, longitude = self.longitude)
            try:
                self.__current_weather_json: Dict[str, Any] | None = self.__weather.get_response()
            except requests.HTTPError as err:
                abort(500, message = str(err))
            else: #Runs if everything went fine with the request to WeatherAPI
                #Everything went fine with the request to weatherAPI. Now, we will catch the requested data.
                try:
                    self.__location: str = self.__current_weather_json['location']['name'] + ', ' + self.__current_weather_json['location']['country']
                    self.__temp_c: float = self.__current_weather_json['current']['temp_c']
                    self.__wind_kph: float = self.__current_weather_json['current']['wind_kph']
                    self.__pressure_mb: float = self.__current_weather_json['current']['pressure_mb']
                    self.__humidity: float = self.__current_weather_json['current']['humidity']
                    self.__uv: float = self.__current_weather_json['current']['uv']
                    self.__wind_dir: float | int = DataHandler.get_simple_direction(self.__current_weather_json['current']['wind_dir'])
                    self.__precipitation: float = self.__current_weather_json['current']['precip_mm']
                    self.__dirty_is_day: int = self.__current_weather_json['current']['is_day']
                    self.__is_day: str = 'yes' if bool(self.__dirty_is_day) else 'no'
                except Exception as err:
                    abort(500, message = f'Something went wrong on the server.\nStatus: {err}')
                #Now, we will lead with the ionizing radiation request
                for mut in range(1, 6):
                    try:
                        self.__ionizing_radiation: IonizingRadiationRequest = IonizingRadiationRequest(latitude = self.latitude,
                                                                                                    longitude = self.longitude,
                                                                                                    radius = 2 * mut * self.__std_radius)
                        self.__current_ir_json: List[Dict[str, Any]] | None = self.__ionizing_radiation.get_response()
                    except requests.HTTPError as err:
                        abort(500, message = str(err))
                    else:
                        if len(self.__current_ir_json) > 0:
                            self.__real_radius: int = 2 * mut * self.__std_radius
                            break
                if len(self.__current_ir_json) == 0:
                    self.__ionizing_radiation_data: str = "N/A" #The JSON don't have any data from inside a circle with radius of 100km with that point on the center.
                else:
                    #If the json is filed with data, we have this case over here. At such scenario, we get the average value of the cpm ionizing radiation measurement.
                    self.__list_of_ir: List[Dict[str, Any]] = DataHandler.clean_radiation_JSON(self.__current_ir_json)
                    if len(self.__list_of_ir) == 0:
                        self.__ionizing_radiation_data: str = "N/A" #The json doesn't deal with cpm (our unit).
                    else:
                        self.__coeficient_var: float = DataHandler.get_coeficient_of_var(self.__list_of_ir)
                        self.__ionizing_radiation_data: float = DataHandler.get_fair_radiation(self.__list_of_ir, radius = self.__real_radius) #Average of the ionizing radiations with cpm as unit.
            
            self.__BASE_JSON: Dict[str, Any] = {
                "location" : self.__location,
                "temperature(°C)" : self.__temp_c,
                "wind_speed(km/h)" : self.__wind_kph,
                "wind_dir(deg)" : self.__wind_dir,
                "pressure(mb)" : self.__pressure_mb,
                "humidity(%)" : self.__humidity,
                "uv" : self.__uv,
                "precipitation(mmHg)" : self.__precipitation,
                "is_day" : self.__is_day,
                "ionizing_radiation(cpm)" : self.__ionizing_radiation_data
            } #This is the most basic json that the server will return to the user.

            if self.detail_bool: # The user requested detailed data about the environment right now.
                
                del self.__BASE_JSON['ionizing_radiation(cpm)']
                self.__BASE_JSON.update(
                                {
                                "temperature" : {"°C" : self.__temp_c, "°F" : DataHandler.transform_c_in_f(self.__temp_c),"k" : DataHandler.transform_c_in_k(self.__temp_c)},
                                "feels_like (Wind_Chill) °C" : DataHandler.get_wind_chill(self.__temp_c, self.__wind_kph),
                                "ionizing_radiation" :{
                                    "value (cpm)" : self.__ionizing_radiation_data,
                                    "coeficient_of_variability" : {
                                        "value (%)": math.floor(100 * self.__coeficient_var),
                                        "heterogeneity_status" : DataHandler.analyze_heterogeneity(self.__coeficient_var)
                                        }
                                    } if self.__ionizing_radiation_data != "N/A" else "N/A"
                                }
                                )
                return self.__BASE_JSON, 200

            else: #It will run if the user don't want details, so the basic json will be returned to the client side.
                
                return self.__BASE_JSON, 200
    
    class ForecastEnvironmentData(ForceGET, Util, Resource):

        def get(self) -> Tuple[Dict[str, Any], int]:

            self.latitude: float = request.args.get("latitude", type = float)
            self.longitude: float = request.args.get("longitude", type = float)

            self.auth(False)

            return {"message": "You've not chosen the detailed option for forecast"}, 200

    def __init__(self, api: Api, **kwargs):
        api.add_resource(kwargs['EnvironmentDataNow'], "/actual_environment")
        api.add_resource(kwargs['ForecastEnvironmentData'], "/forecast_environment")