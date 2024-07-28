from falkordb_gemini_kg.models import GenerativeModel
from falkordb_gemini_kg.agents import Agent
from .orchestrator_runner import OrchestratorRunner
from falkordb_gemini_kg.fixtures.prompts import (
    ORCHESTRATOR_SYSTEM,
    ORCHESTRATOR_EXECUTION_PLAN_PROMPT,
)
from falkordb_gemini_kg.helpers import extract_json
from .execution_plan import (
    ExecutionPlan,
)
import logging

logger = logging.getLogger(__name__)


class Orchestrator:

    _agents = []
    _chat = None

    def __init__(self, model: GenerativeModel):
        self._model = model

    def _get_chat(self):
        if self._chat is None:
            self._chat = self._model.with_system_instruction(
                ORCHESTRATOR_SYSTEM.replace(
                    "#AGENTS",
                    ",".join([str(agent) for agent in self._agents]),
                )
            ).start_chat({"response_validation": False})

        return self._chat

    def register_agent(self, agent: Agent):
        self._agents.append(agent)

    def ask(self, question: str):
        return self.runner(question).run()

    def runner(self, question: str) -> OrchestratorRunner:
        plan = self._create_execution_plan(question)

        return OrchestratorRunner(self._get_chat(), self._agents, plan)

    def _create_execution_plan(self, question: str):
        try:
            response = self._get_chat().send_message(
                ORCHESTRATOR_EXECUTION_PLAN_PROMPT.replace("#QUESTION", question)
            )

            logger.debug(f"Execution plan response: {response.text}")

            plan = ExecutionPlan.from_json(extract_json(response.text, skip_repair=True))

            logger.debug(f"Execution plan: {plan}")

            return plan
        except Exception as e:
            logger.error(f"Failed to create plan: {e}")
            raise e
