from json import loads
from falkordb_gemini_kg.orchestrator.step import PlanStep, StepBlockType


class ExecutionPlan:

    steps: list[PlanStep] = []

    def __init__(self, steps: list[PlanStep]):
        self.steps = steps

    @staticmethod
    def from_json(json: str | dict) -> "ExecutionPlan":
        if isinstance(json, str):
            json = loads(json)
        return ExecutionPlan([PlanStep.from_json(step) for step in json])

    def find_step(self, step_id: str) -> PlanStep:
        for step in self.steps:
            if step.id == step_id:
                return step
            if step.block == StepBlockType.PARALLEL:
                for sub_step in step.payload.steps:
                    if sub_step.id == step_id:
                        return sub_step
        raise ValueError(f"Step with id {step_id} not found")

    def to_json(self) -> dict:
        return {"steps": [step.to_json() for step in self.steps]}

    def __str__(self) -> str:
        return f"ExecutionPlan(steps={self.to_json()})"
