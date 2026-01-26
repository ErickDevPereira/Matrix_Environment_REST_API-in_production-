import numpy as np
from typing import List

class DataHandler:

    @staticmethod
    def get_avg(values: List[int | float]):
        arr = np.array(values)
        avg = np.average(arr)
        return avg
