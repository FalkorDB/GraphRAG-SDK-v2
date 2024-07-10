from falkordb_gemini_kg.kg import KnowledgeGraph
from .agent import Agent


class KGAgent(Agent):

    _schema = [
        {
            "name": "prompt",
            "type": "string",
            "required": True,
            "description": "The prompt to ask the agent.",
        }
    ]

    def __init__(self, agent_id: str, kg: KnowledgeGraph, introduction: str):
        super().__init__()
        self.agent_id = agent_id
        self.introduction = introduction
        self.kg = kg

    @property
    def agent_id(self) -> str:
        return self._agent_id
    
    @agent_id.setter
    def agent_id(self, value):
        self._agent_id = value

    @property
    def introduction(self) -> str:
        return self._introduction
    
    @introduction.setter
    def introduction(self, value):
        self._introduction = value

    @property
    def _schema(self) -> list[dict]:
        return self._schema
    
    @property
    def kg(self) -> KnowledgeGraph:
        return self._kg
    
    @kg.setter
    def kg(self, value):
        self._kg = value

    def run(self, params: dict):
        return self._kg.ask(params["prompt"])

    def to_orchestrator(self):
        return f"""
---
Agent ID: {self.agent_id}
Knowledge Graph Name: {self._kg.name}

Introduction: {self.introduction}
"""
