import mysql.connector as conn
from typing import Any

class DataDefinitionLanguage:

    def __init__(self, username: str, password: str):
        self.__username: str = username
        self.__password: str = password
        self.__db: conn.PooledMySQLConnection | conn.MySQLConnectionAbstract = conn.connect(
            username = self.__username,
            password = self.__password,
            host = 'localhost'
        ) #Creating a connection to MySQL
        #Creating the database
        self.__cursor: Any = self.__db.cursor()
        self.__cursor.excute("CREATE DATABASE IF NOT EXISTS matrix_environment_db")
        self.__cursor.close()
        self.kill_MySQL_connection(self.__db)
        #Creating a connection to the database
        self.__db = self.get_MySQL_connection()
        #Creating the tables over the database
        self.__cursor: Any = self.__db.cursor()
        self.__cursor.execute("""
                    CREATE TABLE IF NOT EXISTS atmosphere (
                        rec_id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
                        temperature DECIMAL(4, 1) NOT NULL,
                        uv DECIMAL(3, 1) NOT NULL,
                        pressure DECIMAL(5, 1) NOT NULL,
                        humidity TINYINT UNSIGNED NOT NULL,
                        precipitation DECIMAL(5, 1) NOT NULL,
                        wind_speed DECIMAL(4, 1) NOT NULL,
                        cloud TINYINT UNSIGNED NOT NULL,
                    )
                    """)
        self.__cursor.close()
        self.__cursor: Any = self.__db.cursor()
        self.__cursor.execute("""
                    CREATE TABLE IF NOT EXISTS states (
                        rec_id INT UNSIGNED,
                        is_day TINYINT NOT NULL,
                        will_it_rain TINYINT NOT NULL,
                        will_it_snow TINYINT NOT NULL,
                        FOREIGN KEY (rec_id) REFERENCES atmosphere (rec_id)
                    )
                    """)
        self.__cursor.close()
        self.kill_MySQL_connection(self.__db)
    
    def get_MySQL_connection(self) -> conn.PooledMySQLConnection | conn.MySQLConnectionAbstract:
        self.__db: conn.PooledMySQLConnection | conn.MySQLConnectionAbstract = conn.connect(
            username = self.__username,
            password = self.__password,
            host = 'localhost',
            database = 'matrix_environment_db'
        )
        return self.__db
    
    def kill_MySQL_connection(self, conn: conn.PooledMySQLConnection | conn.MySQLConnectionAbstract) -> None:
        conn.close()