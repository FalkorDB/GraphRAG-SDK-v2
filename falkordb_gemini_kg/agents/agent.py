from falkordb_gemini_kg.kg import KnowledgeGraph


class Agent(object):

    @property
    def agent_id(self) -> str:
        pass

    @property
    def introduction(self) -> str:
        pass

    @property
    def _schema(self) -> list[dict]:
        pass

    def run(self, params: dict):
        pass

    def to_orchestrator(self):
        pass
