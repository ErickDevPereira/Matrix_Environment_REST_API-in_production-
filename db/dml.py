from abc import ABC, abstractmethod
from mysql.connector import CMySQLConnection, MySQLConnection, MySQLCursor

class DataManipulationLanguage:

    class DataSet(ABC):

        @abstractmethod
        def load(self) -> None:
            pass
            
        @abstractmethod
        def rm(self) -> None:
            pass
    
    class RequestForecastToken(DataSet):

        def load(self,
                MySQL_conn: CMySQLConnection | MySQLConnection,
                token: str) -> None:

            self.__cursor: MySQLCursor = MySQL_conn.cursor()
            self.__cursor.execute("INSERT INTO request_forecast_token (req_token) VALUES (%s)", (token,))
            MySQL_conn.commit()
            self.__cursor.close()

        def rm(self, MySQL_conn: CMySQLConnection | MySQLConnection, token: str) -> None:
            self.__cursor: MySQLCursor = MySQL_conn.cursor()
            self.__cursor.execute("DELETE FROM request_forecast_token WHERE req_token = %s", (token,))
            MySQL_conn.commit()
            self.__cursor.close()

    class Atmosphere(DataSet):

        def load(self,
                MySQL_conn: CMySQLConnection | MySQLConnection,
                rec_id: str,
                temperature: float,
                uv: float,
                pressure: float | int,
                humidity: int,
                precipitation: float,
                wind_speed: float,
                cloud: int) -> None:
            
            self.__cursor: MySQLCursor = MySQL_conn.cursor()
            self.__cursor.execute("""
                                INSERT INTO atmosphere (rec_id, temperature, uv, pressure, humidity, precipitation, wind_speed, cloud)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                  """, (rec_id, temperature, uv, pressure, humidity, precipitation, wind_speed, cloud))
            MySQL_conn.commit()
            self.__cursor.close()
        
        def rm(self, MySQL_conn: CMySQLConnection | MySQLConnection, token: str) -> None:
            self.__cursor: MySQLCursor = MySQL_conn.cursor()
            self.__cursor.execute("DELETE FROM atmosphere WHERE RIGHT(rec_id, 16) = %s", (token,))
            MySQL_conn.commit()
            self.__cursor.close()
        
    class State(DataSet):

        def load(self,
                MySQL_conn: CMySQLConnection | MySQLConnection,
                rec_id: int,
                is_day: int,
                will_it_rain: int,
                will_it_snow: int,
                time: str) -> None:

            self.__cursor: MySQLCursor = MySQL_conn.cursor()
            self.__cursor.execute("""
                                INSERT INTO states (rec_id, is_day, will_it_rain, will_it_snow, time)
                                VALUES (%s, %s, %s, %s, %s)
                                """, (rec_id, is_day, will_it_rain, will_it_snow, time))
            MySQL_conn.commit()
            self.__cursor.close()
        
        def rm(self, MySQL_conn: CMySQLConnection | MySQLConnection, token: str) -> None:
            self.__cursor: MySQLCursor = MySQL_conn.cursor()
            self.__cursor.execute("DELETE FROM states WHERE RIGHT(rec_id, 16) = %s", (token,))
            MySQL_conn.commit()
            self.__cursor.close()
    
    class Opinion(DataSet):

        def load(self,
                MySQL_conn: CMySQLConnection | MySQLConnection,
                name: str,
                text: str,
                token: str,
                latitude: str,
                longitude: str) -> None:
            self.__cursor: MySQLCursor = MySQL_conn.cursor()
            self.__cursor.execute("INSERT INTO opinions (name, text, token, latitude, longitude) VALUES (%s, %s, %s, %s, %s)", (name, text, token, latitude, longitude))
            MySQL_conn.commit()
            self.__cursor.close()

        def rm(self, MySQL_conn: CMySQLConnection | MySQLConnection, token: str) -> None:
            self.__cursor: MySQLCursor = MySQL_conn.cursor()
            self.__cursor.execute("DELETE FROM opinions WHERE token = %s", (token,))
            MySQL_conn.commit()
            self.__cursor.close()
        
        def edit(self, MySQL_conn: CMySQLConnection | MySQLConnection, token: str, new_text: str) -> None:
            self.__cursor: MySQLCursor = MySQL_conn.cursor()
            self.__cursor.execute("UPDATE opinions SET text = %s WHERE token = %s", (new_text, token))
            MySQL_conn.commit()
            self.__cursor.close()