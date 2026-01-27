import numpy as np
from typing import List, Dict, Any
import pandas as pd
import datetime

class DataHandler:

    @staticmethod
    def get_fair_radiation(rad_data: List[Dict[str, float]], radius: int) -> float:
        #Vector of displacements
        displacements: np.ndarray = np.array([np.array([rad_data[_]['lon'], rad_data[_]['lat']]) for _ in range(len(rad_data))])
        #Vector of weights
        weights: np.ndarray = np.array([radius - np.sqrt(np.inner(displacements[_], displacements[_])) for _ in range(len(displacements))])
        #Vector of radiations
        radiations: np.ndarray = np.array([rad["radiation"] for rad in rad_data])
        #Real data average taken from the formula avg = <weights, radiations> / sum(weights)
        real_avg: float = np.inner(weights, radiations) / np.sum(weights)
        return real_avg
    
    @staticmethod
    def get_coeficient_of_var(rad_data: List[Dict[str, float]]) -> float:
        #vector with every radiation inside the circle
        radiations: np.ndarray = np.array([rad['radiation'] for rad in rad_data])
        #getting average radiation
        avg_rad: float = np.sum(radiations) / len(radiations)
        #getting average deviation
        avg_deviation: float = np.sqrt(np.sum((radiations - avg_rad) ** 2) / len(radiations))
        #getting variability coeficient
        CV: float = avg_deviation / avg_rad
        return CV

    @staticmethod
    def clean_radiation_JSON(input_JSON : List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    
        if not isinstance(input_JSON, list):
            raise TypeError("The JSON must be an array of dictionaries")
        
        """Some supporters of the safecast API are not giving longitude or unit data, which are part of 
        the heart of the operations in my API, so I decided to take these dictionaries out of way."""
        cols: List[str] = ["latitude", "longitude", "value", "captured_at", "unit"]
        for _ in range(len(input_JSON)):
            for arg in cols:
                if arg not in input_JSON[_]:
                    input_JSON[_] = "TO_DELETE" #Marking each item of the list with TO_DELETE when the structure of the dictionary is inconsistent.
                    break
        input_JSON: List[Dict[str, Any]] = [data for data in input_JSON if data != "TO_DELETE"] #JSON without the insconsistent dictionaries

        BASE: Dict[str, List[Any]] = {
            "latitude" : [record['latitude'] for record in input_JSON],
            "longitude" : [record['longitude'] for record in input_JSON],
            "value" : [record['value'] for record in input_JSON],
            "date" : [record['captured_at'] for record in input_JSON],
            "unit" : [record['unit'] for record in input_JSON]
        } #Dictionary in a format accepted by Pandas

        df: pd.DataFrame = pd.DataFrame(BASE) #Creating the dataframe
        df['date'] = pd.to_datetime(df['date'], format = 'mixed') #Improving date data

        #Dropping records with NaN, None or NaT from the dataframe that will export a JSON afterwards.
        df.dropna(inplace = True)

        #Cleaning records with inconsistent unit and old data.
        for index in df.index:
            #Taking out records without cpm as measure
            if df.loc[index, 'unit'] not in ('cpm', ' cpm', 'cpm '):
                df.drop(index, inplace = True)
                continue
            
            YEAR_RIGHT_NOW: int = datetime.datetime.now().year
            ACCEPTED_YEARS: int = 5
            year_in_cell: int = int(str(df.loc[index, 'date'])[:4])
            if not year_in_cell >= YEAR_RIGHT_NOW - ACCEPTED_YEARS:
                df.drop(index, inplace = True)
                continue

        #This is the cleaned JSON that is useful on the API.
        output_JSON: List[Dict[str, Any]] = [
                {
                "lat" : df.loc[ind, "latitude"],
                "lon" : df.loc[ind, "longitude"],
                "radiation" : df.loc[ind, "value"]
                } for ind in df.index
            ]
        
        return output_JSON
    
    @staticmethod
    def get_simple_direction(wind_dir: str) -> float | int:
        
        match(wind_dir):

            case 'N':
                return 0
            
            case 'NNE':
                return 22.5
            
            case 'NE':
                return 45
            
            case 'ENE':
                return 67.5
            
            case 'E':
                return 90
            
            case 'ESE':
                return 112.5
            
            case 'SE':
                return 135
            
            case 'SSE':
                return 157.5
            
            case 'S':
                return 180
            
            case 'SSW':
                return 202.5
            
            case 'SW':
                return 225
            
            case 'WSW':
                return 247.5
            
            case 'W':
                return 270
            
            case 'WNW':
                return 292.5
            
            case 'NW':
                return 315
            
            case 'NNW':
                return 337.5
            
            case _:
                return "N/A"

    @staticmethod
    def transform_c_in_f(temp: float | int) -> float:
        #Formula that converts °C to F
        F: float = temp * (9/5) + 32
        return F
    
    @staticmethod
    def transform_c_in_k(temp: float | int) -> float:
        #Formula that converts °C to kelvin
        K: float = temp + 273.15
        return K

    @staticmethod
    def get_wind_chill(temp: float | int, wind_speed: float | int) -> Dict[str, None | float | bool]:

        #This model will predict the feels like temperature if the temperature is <= 10°C and the wind speed is >= 4.8 km/h, otherwise, the prediction won't be good.
        if temp <= 10.0 and wind_speed >= 4.8:
        
            piece: float = wind_speed ** (16/100)
            WC: float = 13.12 + 0.6215 * temp - 11.37 * piece + 0.3965 * temp * piece #Returns the temperature in °C
            return {"temperature" : WC, "valid_case" : True} #JSON with data for the valid case
        
        return {"temperature" : None, "valid_case" : False} #JSON with None for the invalid case.
    
    @staticmethod
    def analyze_heterogeneity(vc : float) -> str:

        if vc < 0.1:
            return "low"
        elif vc < 0.3:
            return "regular"
        else:
            return "high"

if __name__ == '__main__':
    print(DataHandler.get_heat_index(30, 78))