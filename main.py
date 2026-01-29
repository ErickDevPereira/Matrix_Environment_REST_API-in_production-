from flask import Flask
from flask_restful import Api
from typing import Dict, List, Any
import os
from db import IoMySQL, DataDefinitionLanguage
import mysql.connector as MySQL

class __Main:

    def __init__(self, safe_api_token: str, weather_api_token: str):
        self.__app: Flask = Flask(__name__)
        self.__api: Api = Api(self.__app)
        self.__safe_api_token: str = safe_api_token
        self.__weather_api_token: str = weather_api_token
    
    @property
    def app(self) -> Flask:
        return self.__app
    
    @property
    def api(self) -> Api:
        return self.__api
    
    def token_gate(self) -> Dict[str, str]:
        tokens: Dict[str, str] = {
                "radiationAPI": self.__safe_api_token,
                "weatherAPI": self.__weather_api_token
                }
        return tokens

if __name__ == "__main__":
    try:
        FILE: Any = open("src/tokens.txt", 'r')
        LINES: List[str] = FILE.readlines()
        FILE.close()
        safe_api_token: str = LINES[1][:-1]
        weather_api_token: str = LINES[-1]
    except Exception as err:
        #Reading the tokens through I/O if the file isn't defined or has a problem.
        print(f"Couldn't read a file with the tokens. Please, give the correct tokens.\n{err}")
        safe_api_token: str = input("Your token to safe API:  ")
        weather_api_token: str = input("Your token to weather API:  ")
        
        if not os.path.exists('src'):
            os.mkdir("src")
        
        FILE: Any = open("src/tokens.txt", 'w')
        FILE.write("safeapi\n" + safe_api_token + "weatherapi\n" + weather_api_token)
        FILE.close()
    finally:
        #Connecting to the database and automating stuff.
        while True:
            try:
                MySQL_username: str = input("Username to MySQL (you can try 'root' if you don't know it):  ") #MySQL username
                MySQL_password: str = input("Password to MySQL:  ") #MySQL password
                ddl = DataDefinitionLanguage(MySQL_username, MySQL_password) #Automate the creation of the database and its tables if they don't exist.
            except MySQL.errors.ProgrammingError:
                print("The username or password is wrong! Try again")
            else:
                FILE: Any = open("src/mysql_credentials.txt", 'w')
                FILE.write(f"username:\n{MySQL_username}\npassword:\n{MySQL_password}") #Writing data on the file
                FILE.close()
                break
        #Creating the API itself
        server: __Main = __Main(safe_api_token = safe_api_token, weather_api_token = weather_api_token)
        from http_logic import HTTP
        ENVIRONMENT_DATA_NOW: HTTP.EnvironmentDataNow = HTTP.EnvironmentDataNow #importing the class that has the HTTP methods for the /actual_environment route.
        FORECAST_ENVIRONMENT_DATA: HTTP.ForecastEnvironmentData = HTTP.ForecastEnvironmentData
        OPINION: HTTP.Opinions = HTTP.Opinions
        http_initializer: HTTP = HTTP(server.api, EnvironmentDataNow = ENVIRONMENT_DATA_NOW, ForecastEnvironmentData = FORECAST_ENVIRONMENT_DATA, Opinions = OPINION)
        server.app.run(debug = True, use_reloader = False)
        IoMySQL.remove_credentials()