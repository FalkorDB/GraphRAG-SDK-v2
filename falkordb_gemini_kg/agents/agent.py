from abc import ABC, abstractmethod
class Agent(ABC):

    @property
    def agent_id(self) -> str:
        pass

    @property
    def introduction(self) -> str:
        pass

    @property
    def interface(self) -> list[dict]:
        pass

    @abstractmethod
    def run(self, params: dict) -> dict:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass
