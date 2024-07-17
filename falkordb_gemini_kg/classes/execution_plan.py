from json import loads


class StepBlockType:
    PARALLEL = "parallel"
    PROMPT_AGENT = "prompt_agent"
    SUMMARY = "summary"

    @staticmethod
    def from_str(text: str) -> "StepBlockType":
        if text == StepBlockType.PARALLEL:
            return StepBlockType.PARALLEL
        elif text == StepBlockType.PROMPT_AGENT:
            return StepBlockType.PROMPT_AGENT
        elif text == StepBlockType.SUMMARY:
            return StepBlockType.SUMMARY


class PromptAgentProperties:
    agent: str
    prompt: str
    response: str | None = None

    def __init__(self, agent: str, prompt: str, response: str | None = None):
        self.agent = agent
        self.prompt = prompt
        self.response = response

    @staticmethod
    def from_json(json: dict) -> "PromptAgentProperties":
        return PromptAgentProperties(
            json["agent"], json["prompt"], json.get("response")
        )

    def to_json(self) -> dict:
        return {
            "agent": self.agent,
            "prompt": self.prompt,
            "response": self.response,
        }


class ParallelProperties:
    steps: list["PlanStep"]

    def __init__(self, steps: list["PlanStep"]):
        self.steps = steps

    @staticmethod
    def from_json(json: dict) -> "ParallelProperties":
        return ParallelProperties([PlanStep.from_json(step) for step in json["steps"]])

    def to_json(self) -> dict:
        return {"steps": [step.to_json() for step in self.steps]}


class PlanStep:
    id: str
    block: StepBlockType
    properties: PromptAgentProperties | ParallelProperties

    def __init__(
        self,
        id: str,
        block: StepBlockType,
        properties: PromptAgentProperties | ParallelProperties,
    ):
        self.id = id
        self.block = block
        self.properties = properties

    @staticmethod
    def from_json(json: dict) -> "PlanStep":
        block = StepBlockType.from_str(json["block"])
        if block == StepBlockType.PROMPT_AGENT:
            properties = PromptAgentProperties.from_json(json["properties"])
        elif block == StepBlockType.PARALLEL:
            properties = ParallelProperties.from_json(json["properties"])
        elif block == StepBlockType.SUMMARY:
            properties = None
        else:
            raise ValueError(f"Unknown block type: {block}")
        return PlanStep(json["id"], block, properties)

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "block": self.block,
            "properties": self.properties.to_json() if self.properties else None,
        }


class ExecutionPlan:

    steps = []

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
                for sub_step in step.properties.steps:
                    if sub_step.id == step_id:
                        return sub_step
        raise ValueError(f"Step with id {step_id} not found")

    def to_json(self) -> dict:
        return {"steps": [step.to_json() for step in self.steps]}

    def __str__(self) -> str:
        return f"ExecutionPlan(steps={self.to_json()})"