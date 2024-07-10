from falkordb_gemini_kg.agents import Agent
from falkordb_gemini_kg.models import GenerativeModelChatSession
from falkordb_gemini_kg.classes.execution_plan import (
    ExecutionPlan,
    PlanStep,
    StepBlockType,
)
from falkordb_gemini_kg.models.model import GenerationResponse
from concurrent.futures import ThreadPoolExecutor, wait
from falkordb_gemini_kg.fixtures.prompts import ORCHESTRATOR_SUMMARY_PROMPT
import logging

logger = logging.getLogger(__name__)


class OrchestratorRunner:

    def __init__(
        self,
        chat: GenerativeModelChatSession,
        agents: list[Agent],
        plan: ExecutionPlan,
        config: dict = {
            "max_workers": 16,
        },
    ):
        self._chat = chat
        self._agents = agents
        self._plan = plan
        self._config = config

    def run(self) -> GenerationResponse:
        for step in self._plan.steps[:-1]:
            self._run_step(step)

        return self._run_step(self._plan.steps[-1])

    def _run_summary(self):
        logger.debug(f"Execution plan summary: {self._plan.to_json()}")
        return self._chat.send_message(
            ORCHESTRATOR_SUMMARY_PROMPT.replace(
                "#EXECUTION_PLAN", str(self._plan.to_json())
            )
        )

    def _run_step(self, step: PlanStep) -> GenerationResponse:
        if step.block == StepBlockType.PROMPT_AGENT:
            return self._run_prompt_agent(step)
        elif step.block == StepBlockType.PARALLEL:
            self._run_parallel(step)
            return None
        elif step.block == StepBlockType.SUMMARY:
            return self._run_summary()
        else:
            raise ValueError(f"Unknown block type: {step.block}")

    def _run_prompt_agent(self, step: PlanStep):
        agent = next(
            agent for agent in self._agents if agent.agent_id == step.properties.agent
        )
        response = agent.run(step.properties.to_json())
        step.properties.response = response
        return response

    def _run_parallel(self, step: PlanStep):
        tasks = []
        with ThreadPoolExecutor(
            max_workers=min(self._config["max_workers"], len(step.properties.steps))
        ) as executor:
            for step in step.properties.steps:
                tasks.append(executor.submit(self._run_step, step))

        wait(tasks)

        return [task.result() for task in tasks]
