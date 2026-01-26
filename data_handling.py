import numpy as np
from typing import List, Dict

class DataHandler:

    @staticmethod
    def get_fair_radiation(rad_data: List[Dict[str, float]], radius: int):
        #Vector of displacements
        displacements = np.array([np.array([rad_data[_]['lon'], rad_data[_]['lat']]) for _ in range(len(rad_data))])
        #Vector of weights
        weights = np.array([radius - np.sqrt(np.inner(displacements[_], displacements[_])) for _ in range(len(displacements))])
        #Vector of radiations
        radiations = np.array([rad["radiation"] for rad in rad_data])
        #Real data average taken from the formula avg = <weights, radiations> / sum(weights)
        real_avg = np.inner(weights, radiations) / np.sum(weights)
        return real_avg