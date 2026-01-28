from os import remove, path
from typing import Tuple, Any, List

class IoMySQL:

    @staticmethod
    def get_mysql_credentials() -> Tuple[str, ...]:
        FILE: Any = open("src/mysql_credentials.txt", "r")
        lines: List[str] = FILE.readlines()
        FILE.close()
        username: str = lines[1][:-1]
        password: str =lines[-1]
        return username, password
    
    @staticmethod
    def remove_credentials() -> None:
        if path.exists("src/mysql_credentials.txt"):
            remove("src/mysql_credentials.txt")