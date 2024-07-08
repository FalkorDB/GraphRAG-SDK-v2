from falkordb_gemini_kg.models import GenerativeModel
from falkordb_gemini_kg.classes.agent import Agent
from falkordb_gemini_kg.classes.orchestrator_runner import OrchestratorRunner
from falkordb_gemini_kg.fixtures.prompts import (
    ORCHESTRATOR_SYSTEM,
    ORCHESTRATOR_EXECUTION_PLAN_PROMPT,
)
from falkordb_gemini_kg.helpers import extract_json
from falkordb_gemini_kg.classes.execution_plan import (
    ExecutionPlan,
    PlanStep,
    StepBlockType,
)


class Orchestrator:

    _agents = []
    _chat = None

    def __init__(self, model: GenerativeModel):
        self._model = model

    def register_agent(self, agent: Agent):
        self._agents.append(agent)

    def ask(self, question: str):

        self._chat = self._model.with_system_instruction(
            ORCHESTRATOR_SYSTEM.replace(
                "#AGENTS", ",".join([agent.to_orchestrator() for agent in self._agents])
            )
        ).start_chat({"response_validation": False})

        plan = self._create_execution_plan(question)

        runner = OrchestratorRunner(self._chat, self._agents, plan)

        return runner

    def _create_execution_plan(self, question: str):
        response = self._chat.send_message(
            ORCHESTRATOR_EXECUTION_PLAN_PROMPT.replace("#QUESTION", question)
        )

        plan = ExecutionPlan.from_json(extract_json(response))

        return plan
