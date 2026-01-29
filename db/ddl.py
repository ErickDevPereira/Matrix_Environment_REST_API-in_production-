import mysql.connector as conn
from typing import Any

class DataDefinitionLanguage:

    def __init__(self, username: str, password: str):
        self.__username: str = username
        self.__password: str = password
        self.__db: conn.CMySQLConnection | conn.MySQLConnection = conn.connect(
            username = self.__username,
            password = self.__password,
            host = 'localhost'
        ) #Creating a connection to MySQL
        #Creating the database
        self.__cursor: Any = self.__db.cursor()
        self.__cursor.execute("CREATE DATABASE IF NOT EXISTS matrix_environment_db")
        self.__cursor.close()
        self.__kill_MySQL_connection(self.__db)
        #Creating a connection to the database
        self.__db = self.__get_MySQL_connection(self.__username, self.__password)
        #Creating the tables over the database
        self.__cursor =  self.__db.cursor()
        self.__cursor.execute("""
                    CREATE TABLE IF NOT EXISTS request_forecast_token (
                        req_token VARCHAR(16) PRIMARY KEY
                    )
                    """)
        self.__cursor.close()
        self.__cursor = self.__db.cursor()
        self.__cursor.execute("""
                    CREATE TABLE IF NOT EXISTS opinions (
                        opnion_id INT PRIMARY KEY AUTO_INCREMENT,
                        name VARCHAR(100),
                        text VARCHAR(1024) NOT NULL,
                        token VARCHAR(16) NOT NULL,
                        latitude VARCHAR(6) NOT NULL,
                        longitude VARCHAR(7) NOT NULL,
                        post_date DATETIME DEFAULT NOW(),
                        FOREIGN KEY (token) REFERENCES request_forecast_token (req_token)
                    )
                            """)
        self.__cursor.close()
        self.__cursor: Any = self.__db.cursor()
        self.__cursor.execute("""
                    CREATE TABLE IF NOT EXISTS atmosphere (
                        rec_id VARCHAR(19) PRIMARY KEY,
                        temperature DECIMAL(4, 1) NOT NULL,
                        uv DECIMAL(3, 1) NOT NULL,
                        pressure DECIMAL(5, 1) NOT NULL,
                        humidity TINYINT UNSIGNED NOT NULL,
                        precipitation DECIMAL(5, 1) NOT NULL,
                        wind_speed DECIMAL(4, 1) NOT NULL,
                        cloud TINYINT UNSIGNED NOT NULL
                    )
                    """)
        self.__cursor.close()
        self.__cursor: Any = self.__db.cursor()
        self.__cursor.execute("""
                    CREATE TABLE IF NOT EXISTS states (
                        rec_id VARCHAR(19),
                        is_day TINYINT NOT NULL,
                        will_it_rain TINYINT NOT NULL,
                        will_it_snow TINYINT NOT NULL,
                        time DATETIME NOT NULL,
                        FOREIGN KEY (rec_id) REFERENCES atmosphere (rec_id)
                    )
                    """)
        self.__cursor.close()
        self.__kill_MySQL_connection(self.__db)
    
    def __get_MySQL_connection(self, username: str, password: str) -> conn.CMySQLConnection | conn.MySQLConnection:
        self.__db: conn.CMySQLConnection | conn.MySQLConnection = conn.connect(
            username = username,
            password = password,
            host = 'localhost',
            database = 'matrix_environment_db'
        )
        return self.__db
    
    def __kill_MySQL_connection(self, conn: conn.CMySQLConnection | conn.MySQLConnection) -> None:
        conn.close()