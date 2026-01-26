import numpy as np
from typing import List, Dict, Any
import pandas as pd
import datetime

class DataHandler:

    @staticmethod
    def get_fair_radiation(rad_data: List[Dict[str, float]], radius: int) -> float:
        #Vector of displacements
        displacements = np.array([np.array([rad_data[_]['lon'], rad_data[_]['lat']]) for _ in range(len(rad_data))])
        #Vector of weights
        weights = np.array([radius - np.sqrt(np.inner(displacements[_], displacements[_])) for _ in range(len(displacements))])
        #Vector of radiations
        radiations = np.array([rad["radiation"] for rad in rad_data])
        #Real data average taken from the formula avg = <weights, radiations> / sum(weights)
        real_avg = np.inner(weights, radiations) / np.sum(weights)
        return real_avg

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