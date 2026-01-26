from typing import Dict, Any, List
from abc import ABC, abstractmethod

class RequestApi(ABC):

    def __init__(self, latitude: int | float, longitude: int | float):
        
        for arg in (latitude, longitude):
            if not isinstance(arg, (int, float)):
                raise TypeError('The arguments can either be float or int, nothing else')
            
        self.__latitude: int | float = latitude
        self.__longitude: int | float = longitude

    @property
    def latitude(self) -> float | int:
        return self.__latitude
    
    @property
    def longitude(self) -> float | int:
        return self.__longitude

    @abstractmethod
    def get_response(self) -> List[Dict[str, Any]] | Dict[str, Any] | None: #This method will be responsible for processing and returning a response.
        pass