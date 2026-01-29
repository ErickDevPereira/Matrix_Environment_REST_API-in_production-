from typing import Dict, Tuple, List, Any
from mysql.connector import CMySQLConnection, MySQLConnection

class DataQueryLanguage:

    class Forecast:

        @staticmethod
        def get_avgs(db: CMySQLConnection | MySQLConnection, token: str) -> Dict[str, Dict[str, float]]:
            cursor: Any = db.cursor()
            SQL: str = """
                        SELECT
                            sq1.day,
                            sq1.avg_temperature,
                            sq1.avg_humidity,
                            sq1.avg_pressure,
                            sq1.avg_wind_speed,
                            sq1.avg_precipitation,
                            sq1.tot_precipitation,
                            sq2.avg_uv
                        FROM
                            (SELECT
                                DATE(s.time) AS day,
                                AVG(a.temperature) AS avg_temperature,
                                AVG(a.humidity) AS avg_humidity,
                                AVG(a.pressure) AS avg_pressure,
                                AVG(a.wind_speed) AS avg_wind_speed,
                                AVG(a.precipitation) AS avg_precipitation,
                                SUM(a.precipitation) AS tot_precipitation,
                                CASE
                                    WHEN SUM(s.will_it_rain) = 0 THEN 0
                                    ELSE 1
                                END AS will_it_rain,
                                CASE
                                    WHEN SUM(s.will_it_snow) = 0 THEN 0
                                    ELSE 1
                                END AS will_it_snow
                            FROM
                                atmosphere AS a INNER JOIN states AS s
                                ON a.rec_id = s.rec_id
                            WHERE
                                RIGHT(s.rec_id, 16) = %s
                            GROUP BY
                                day
                            ORDER BY
                                day ASC) AS sq1
                            INNER JOIN
                            (SELECT
                                AVG(a.uv) AS avg_uv,
                                DATE(s.time) AS day
                            FROM
                                atmosphere AS a INNER JOIN states AS s
                                ON a.rec_id = s.rec_id
                            WHERE
                                s.is_day = 1 AND RIGHT(s.rec_id, 16) = %s
                            GROUP BY
                                day) AS sq2
                            ON sq1.day = sq2.day
                        ORDER BY
                            sq1.day
                        """
            cursor.execute(SQL, (token, token))
            days: List[Tuple[str, float, float, float, float, float, float, float]] = cursor.fetchall()
            cursor.close()
            treated_data: Dict[str, Dict[str, float]] = dict()
            for day in days:
                treated_data.update({
                    str(day[0]) : {'average_temperature(°C)' : float(day[1]),
                              'average_humidity(%)' : float(day[2]),
                              'average_pressure(mb)' : float(day[3]),
                              'average_wind_speed(km/h)' : float(day[4]),
                              'average_precipitation(mm)' : float(day[5]),
                              'total_of_precipitation(mm)' : float(day[6]),
                              'average_uv_during_day' : float(day[7])}
                            })
            return treated_data

        @staticmethod
        def get_extremes(db: CMySQLConnection | MySQLConnection, token: str) -> Dict[str, Dict[str, Dict[str, float | int]]]:
            cursor: Any = db.cursor()
            SQL: str = """
                        SELECT
                            DATE(s.time) AS day,
                            MAX(a.temperature),
                            MIN(a.temperature),
                            MAX(a.pressure),
                            MIN(a.pressure),
                            MAX(a.humidity),
                            MIN(a.humidity),
                            MAX(a.wind_speed),
                            MIN(a.wind_speed)
                        FROM
                            atmosphere AS a INNER JOIN states AS s
                            ON a.rec_id = s.rec_id
                        WHERE
                            RIGHT(a.rec_id, 16) = %s
                        GROUP BY
                            day
                        ORDER BY
                            day ASC
                        """
            cursor.execute(SQL, (token,))
            days: List[Tuple[str, float, float, float, float, int, int, float, float]] = cursor.fetchall()
            cursor.close()
            treated_data: Dict[str, Dict[str, Dict[str, float | int]]] = dict()
            for day in days:
                treated_data.update({
                    str(day[0]) : {
                        "temperature(°C)": {
                            "max" : float(day[1]),
                            "min" : float(day[2])
                        },
                        "pressure(mb)": {
                            "max" : float(day[3]),
                            "min" : float(day[4])
                        },
                        "humidity(%)" : {
                            "max" : int(day[5]),
                            "min" : int(day[6])
                        },
                        "wind_speed(km/h)" : {
                            "max" : float(day[7]),
                            "min" : float(day[8])
                        }
                    }
                })
            return treated_data

    class Opinion:

        @staticmethod
        def get_opinions(db: CMySQLConnection | MySQLConnection, latitude: str, longitude: str) -> List[str]:

            cursor: Any = db.cursor()
            cursor.execute(
                        """
                        SELECT
                            text, post_date
                        FROM
                            opinions
                        WHERE
                            latitude = %s AND longitude = %s
                        """, (latitude, longitude)
                        )
            texts: List[Tuple[str]] = cursor.fetchall()
            cursor.close()
            JSON = [{"text": text[0], "date": str(text[1])} for text in texts]
            return JSON
        
        @staticmethod
        def check_token(db: CMySQLConnection | MySQLConnection, token: str) -> bool:

            cursor: Any = db.cursor()
            cursor.execute("SELECT token FROM opinions WHERE token = %s", (token,))
            data = cursor.fetchall()
            
            return bool(data)