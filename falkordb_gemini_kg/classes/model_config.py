class KnowledgeGraphModelStepConfig:

    def __init__(self, model: str, generation_config: dict | None = None):
        self.model = model
        self.generation_config = generation_config


class KnowledgeGraphModelConfig:

    def __init__(
        self,
        extract_data: KnowledgeGraphModelStepConfig | None = None,
        cypher_generation: KnowledgeGraphModelStepConfig | None = None,
        qa: KnowledgeGraphModelStepConfig | None = None,
    ):
        self.extract_data = extract_data
        self.cypher_generation = cypher_generation
        self.qa = qa

    @staticmethod
    def from_dict(d: dict):
        model = d.get("model")
        generation_config = d.get("generation_config")
        extract_data = KnowledgeGraphModelStepConfig(
            model=model, generation_config=generation_config
        )
        cypher_generation = KnowledgeGraphModelStepConfig(
            model=model, generation_config=generation_config
        )
        qa = KnowledgeGraphModelStepConfig(
            model=model, generation_config=generation_config
        )
        return KnowledgeGraphModelConfig(
            extract_data=extract_data,
            cypher_generation=cypher_generation,
            qa=qa,
        )
