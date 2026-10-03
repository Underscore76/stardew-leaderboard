from pydantic import BaseModel
from abc import abstractmethod, ABC


class StardewBaseModel(BaseModel, ABC):
    @property
    @abstractmethod
    def pk(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def sk(self) -> str:
        raise NotImplementedError
