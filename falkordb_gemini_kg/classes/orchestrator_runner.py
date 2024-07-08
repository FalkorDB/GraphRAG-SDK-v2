from falkordb_gemini_kg.classes.agent import Agent
from falkordb_gemini_kg.models import GenerativeModelChatSession
from falkordb_gemini_kg.classes.execution_plan import (
    ExecutionPlan,
    PlanStep,
    StepBlockType,
)
from concurrent.futures import ThreadPoolExecutor, wait
from falkordb_gemini_kg.fixtures.prompts import ORCHESTRATOR_SUMMARY_PROMPT


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

    def _run(self):
        for step in self._plan.steps:
            self._run_step(step)

        return self._run_summary()

    def _run_summary(self):
        return self._chat.send_message(
            ORCHESTRATOR_SUMMARY_PROMPT.replace("#EXECUTION_PLAN", self._plan.to_json())
        )

    def _run_step(self, step: PlanStep):
        if step.block == StepBlockType.PROMPT_AGENT:
            return self._run_prompt_agent(step)
        elif step.block == StepBlockType.PARALLEL:
            return self._run_parallel(step)
        else:
            raise ValueError(f"Unknown block type: {step.block}")

    def _run_prompt_agent(self, step: PlanStep):
        agent = next(
            agent for agent in self._agents if agent.id == step.properties.agent_id
        )
        response = agent.ask(step.properties.prompt)
        step.properties.response = response

    def _run_parallel(self, step: PlanStep):
        tasks = []
        with ThreadPoolExecutor(
            max_workers=min(self._config["max_workers"], len(step.properties.steps))
        ) as executor:
            for step in step.properties.steps:
                tasks.append(executor.submit(self._run_step, step))

        wait(tasks)

        return [task.result() for task in tasks]
