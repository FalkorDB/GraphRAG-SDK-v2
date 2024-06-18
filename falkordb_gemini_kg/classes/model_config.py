from vertexai.generative_models import GenerationConfig


class StepModelGenerationConfig:
    def __init__(
        self,
        temperature: float,
        top_p: float,
        top_k: int,
        candidate_count: int,
        max_output_tokens: int,
        stop_sequences: list[str],
    ):
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.candidate_count = candidate_count
        self.max_output_tokens = max_output_tokens
        self.stop_sequences = stop_sequences

    def to_generation_config(self) -> GenerationConfig:
        return GenerationConfig(
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            candidate_count=self.candidate_count,
            max_output_tokens=self.max_output_tokens,
            stop_sequences=self.stop_sequences,
        )


class StepModelConfig:

    def __init__(
        self, model: str, generation_config: StepModelGenerationConfig | None = None
    ):
        self.model = model
        self.generation_config = generation_config


class KnowledgeGraphModelConfig:

    def __init__(
        self,
        extract_data: StepModelConfig | None = None,
        cypher_generation: StepModelConfig | None = None,
        qa: StepModelConfig | None = None,
    ):
        self.extract_data = extract_data
        self.cypher_generation = cypher_generation
        self.qa = qa

    @staticmethod
    def from_dict(d: dict):
        model = d.get("model")
        generation_config = d.get("generation_config")
        extract_data = StepModelConfig(model=model, generation_config=generation_config)
        cypher_generation = StepModelConfig(
            model=model, generation_config=generation_config
        )
        qa = StepModelConfig(model=model, generation_config=generation_config)
        return KnowledgeGraphModelConfig(
            extract_data=extract_data,
            cypher_generation=cypher_generation,
            qa=qa,
        )
