from abc import ABC, abstractmethod
from mysql.connector import CMySQLConnection, MySQLConnection
from typing import Any

class DataManipulationLanguage:

    class DataSet(ABC):

        @abstractmethod
        def load(self) -> None:
            pass
    
    class Atmosphere(DataSet):

        def load(self, MySQL_conn: CMySQLConnection | MySQLConnection) -> None:
            
            self.__cursor: Any = MySQL_conn.cursor()
            self.__cursor.execute("""
                                INSERT INTO atmosphere (temperature, uv, pressure, humidity, precipitation, wind_speed, cloud)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                                  """)
            self.__cursor.commit()
            self.__cursor.close()

    class State(DataSet):

        def load(self, MySQL_conn: CMySQLConnection | MySQLConnection) -> None:

            self.__cursor: Any = MySQL_conn.cursor()
            self.__cursor.execute("""
                                INSERT INTO state (rec_id, is_day, will_it_rain, will_it_snow)
                                VALUES (%s, %s, %s, %s)
                                """)
            self.__cursor.commit()
            self.__cursor.close()