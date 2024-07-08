from falkordb_gemini_kg.kg import KnowledgeGraph


class Agent:

    def __init__(self, id: str, kg: KnowledgeGraph, introduction: str):
        self.id = id
        self._kg = kg
        self._introduction = introduction

    def ask(self, question: str):
        return self._kg.ask(question)

    def to_orchestrator(self):
        return f"""
---
Agent ID: {self.id}
Knowledge Graph Name: {self._kg.name}

Introduction: {self._introduction}
"""
