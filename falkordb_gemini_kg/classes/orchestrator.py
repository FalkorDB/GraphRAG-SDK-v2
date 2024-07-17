from falkordb_gemini_kg.models import GenerativeModel
from falkordb_gemini_kg.agents import Agent
from falkordb_gemini_kg.classes.orchestrator_runner import OrchestratorRunner
from falkordb_gemini_kg.fixtures.prompts import (
    ORCHESTRATOR_SYSTEM,
    ORCHESTRATOR_EXECUTION_PLAN_PROMPT,
)
from falkordb_gemini_kg.helpers import extract_json
from falkordb_gemini_kg.classes.execution_plan import (
    ExecutionPlan,
)
import logging

logger = logging.getLogger(__name__)


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
                "#AGENTS",
                ",".join([agent.to_orchestrator() for agent in self._agents]),
            )
        ).start_chat({"response_validation": False})

        plan = self._create_execution_plan(question)

        runner = OrchestratorRunner(self._chat, self._agents, plan)

        return runner

    def _create_execution_plan(self, question: str):
        try:
            response = self._chat.send_message(
                ORCHESTRATOR_EXECUTION_PLAN_PROMPT.replace("#QUESTION", question)
            )

            logger.debug(f"Execution plan response: {response.text}")

            plan = ExecutionPlan.from_json(extract_json(response.text))

            logger.debug(f"Execution plan: {plan}")

            return plan
        except Exception as e:
            logger.error(f"Failed to create plan: {e}")
            raise e
