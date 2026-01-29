from flask import request
from flask_restful import reqparse, Resource, abort, Api
from typing import Dict, Tuple, Any, List
from abc import ABC, abstractmethod
from external_requests import CurrentWeatherRequest, IonizingRadiationRequest, ForecastWeatherRequest
from data_handling import DataHandler
import requests
import math
from db import DataManipulationLanguage, DataDefinitionLanguage, IoMySQL, DataQueryLanguage
from os import urandom
from mysql.connector import errors, CMySQLConnection, MySQLConnection

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

            self.__forecast_weather: ForecastWeatherRequest = ForecastWeatherRequest(latitude=self.latitude, longitude=self.longitude)
            try:
                self.__full_JSON = self.__forecast_weather.get_response()
            except requests.HTTPError as err:
                abort(500, message = str(err))
            else:
                #Here is the situation when everything went fine with the request to the API.
                self.__filtered_data = self.__full_JSON['forecast']['forecastday']
                self.__db = IoMySQL.get_MySQL_conn() #Gets connection with MySQL.
                self.__dml = DataManipulationLanguage() #Creates a dml object
                self.__token = self.__dml.RequestForecastToken()
                self.__atm = self.__dml.Atmosphere() #Creates an atmosphere object
                self.__states = self.__dml.State()
                self.__id = 0
                while True:
                    try:
                        self.__hex_token = urandom(8).hex()
                        self.__token.load(self.__db, token = self.__hex_token)
                    except errors.IntegrityError:
                        pass
                    else:
                        break
                for day in self.__filtered_data:
                    self.__hours = day['hour']
                    for hour in self.__hours:
                        self.__atm.load(self.__db,
                                        rec_id = str(self.__id) + self.__hex_token,
                                        temperature = hour['temp_c'],
                                        uv = hour['uv'],
                                        pressure = hour['pressure_mb'],
                                        humidity = hour['humidity'],
                                        precipitation = hour['precip_mm'],
                                        wind_speed = hour['wind_kph'],
                                        cloud = hour['cloud'])
                        self.__states.load(self.__db,
                                        rec_id = str(self.__id) + self.__hex_token,
                                        is_day = hour['is_day'],
                                        will_it_rain = hour['will_it_rain'],
                                        will_it_snow = hour['will_it_snow'],
                                        time = str(hour['time'])
                                        )
                        self.__id += 1
                self.__dql = DataQueryLanguage()
                self.__forecast = self.__dql.Forecast()
                self.__SUB_JSON1: Dict[str, Dict[str, float]] = self.__forecast.get_avgs(self.__db, token = self.__hex_token)
                self.__SUB_JSON2: Dict[str, Dict[str, Dict[str, float | int]]] = self.__forecast.get_extremes(self.__db, token = self.__hex_token)
                self.__states.rm(self.__db, token = self.__hex_token) #Deleting data from states table.
                self.__atm.rm(self.__db, token = self.__hex_token) #Deleting data from atmosphere table.
                self.__token.rm(self.__db, token = self.__hex_token)
                self.__db.close() #Closing the connection to the database.
                self.__JSON = {"averages" : self.__SUB_JSON1, "extremes": self.__SUB_JSON2}
                return self.__JSON, 200

    class Opinions(ForceGET, Util, Resource):

        def __init__(self):
            super().__init__() #Calls the constructor of Resource if it exists, doing whatever it needs to do on my class in order to keep the API working.
            self.__opinions_args: reqparse.RequestParser = reqparse.RequestParser()
            self.__msg = lambda field : f'Something went wrong with the field {field}'
            self.__opinions_args.add_argument("name", type = str, help = self.__msg('name'))
            self.__opinions_args.add_argument("text", type = str, help = self.__msg('text'))
            self.__opinions_args.add_argument("token", type = str, help = self.__msg('token'))
            self.__dml = DataManipulationLanguage() #Will be used later on POST and DELETE

        def get(self):
            
            self.latitude: float = request.args.get("latitude", type = float)
            self.longitude: float = request.args.get("longitude", type = float)

            self.auth(False)

            self.__latitude_str: str = f'{self.latitude:.3f}'
            self.__longitude_srt: str = f'{self.longitude:.3f}'
            self.__db = IoMySQL.get_MySQL_conn()
            self.__dql = DataQueryLanguage()
            self.__commments = self.__dql.Opinion().get_opinions(self.__db, self.__latitude_str, self.__longitude_srt)
            self.__db.close()
            if len(self.__commments) == 0:
                return {"message": f"No comments registered for {self.__latitude_str}, {self.__longitude_srt}"}, 200
            else:
                return {"number_of_comments" : len(self.__commments), "comments" : self.__commments}, 200

        def post(self):

            self.latitude: float = request.args.get("latitude", type = float)
            self.longitude: float = request.args.get("longitude", type = float)
            self.auth(False)
            self.__opinion_JSON: Any = self.__opinions_args.parse_args()
            
            if self.__opinion_JSON['text'] is None or self.__opinion_JSON['name'] is None:
                abort(400, message = 'You must give a JSON with fields "text" and "name"')
            
            self.__db = IoMySQL.get_MySQL_conn() #Gets connection with MySQL.
            self.__opinionPOST = self.__dml.Opinion()
            self.__tokenPOST = self.__dml.RequestForecastToken()
            while True:
                    try:
                        self.__token_POST_hex = urandom(8).hex()
                        self.__tokenPOST.load(self.__db, token = self.__token_POST_hex)
                    except errors.IntegrityError:
                        pass
                    else:
                        break
            self.__opinionPOST.load(self.__db,
                                    name = self.__opinion_JSON['name'],
                                    text = self.__opinion_JSON['text'],
                                    token = self.__token_POST_hex,
                                    latitude = f'{self.latitude:.3f}',
                                    longitude = f'{self.longitude:.3f}')
            self.__db.close()
            return {"token" : self.__token_POST_hex, "message": "Save this token with you. You will need it if you wish to delete or edit your comment"}, 201

        def patch(self):

            self.__opinion_JSON: Any = self.__opinions_args.parse_args()
            self.__edit_token: None | str = self.__opinion_JSON['token']
            self.__edit_text: None | str = self.__opinion_JSON['text']

            if self.__edit_token is None or self.__edit_text is None:
                abort(400, message = "You must provide a value for text and token parameters if you want to edit a comment!")
            
            self.__db: CMySQLConnection | MySQLConnection = IoMySQL.get_MySQL_conn() #Gets connection with MySQL.
            self.__dql: DataQueryLanguage = DataQueryLanguage()
            self.__exists: bool = self.__dql.Opinion().check_token(self.__db, self.__edit_token)

            if not self.__exists:
                abort(404, message = "The given token is not linked to any of the opinions on the database!")

            try:
                self.__dml.Opinion().edit(self.__db, new_text = self.__edit_text, token = self.__edit_token)
            except Exception as err:
                abort(500, message = f"Something went wrong on the database or application. Error: {err}")
            else:
                return {"message" : "text was changed with success"}, 200

        def delete(self):

            self.__opinion_JSON: Any = self.__opinions_args.parse_args()
            self.__del_token: None | str = self.__opinion_JSON['token']

            if self.__del_token is None:
                abort(400, message = "You must deliver a token")
            
            self.__db: CMySQLConnection | MySQLConnection = IoMySQL.get_MySQL_conn() #Gets connection with MySQL.
            self.__dql: DataQueryLanguage = DataQueryLanguage()
            self.__exists: bool = self.__dql.Opinion().check_token(self.__db, self.__del_token)
            
            if self.__exists:
                try:
                    self.__dml.Opinion().rm(self.__db, self.__del_token) #Deleting the opinion of the user.
                    self.__dml.RequestForecastToken().rm(self.__db, self.__del_token) #Deleting the token from table of tokens
                except Exception:
                    self.__db.close()
                    abort(500, message = "Something went wrong on the database of the server! Try later")
                else:
                    self.__db.close()
                    return {"message": "The comment was deleted successfully!"}, 200
            self.__db.close()
            abort(400, message = "There is no comment with such token")

    def __init__(self, api: Api, **kwargs):
        api.add_resource(kwargs['EnvironmentDataNow'], "/actual_environment")
        api.add_resource(kwargs['ForecastEnvironmentData'], "/forecast_environment")
        api.add_resource(kwargs['Opinions'], "/my_opinion")
        