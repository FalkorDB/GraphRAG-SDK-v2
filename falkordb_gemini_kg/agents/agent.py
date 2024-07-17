class Agent(object):

    @property
    def agent_id(self) -> str:
        pass

    @property
    def introduction(self) -> str:
        pass

    @property
    def schema(self) -> list[dict]:
        pass

    def run(self, params: dict):
        pass

    def to_orchestrator(self):
        pass
