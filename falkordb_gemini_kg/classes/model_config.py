class KnowledgeGraphModelStepConfig():

    def __init__(self, model: str, generation_config: dict):
        self.model = model
        self.generation_config = generation_config


class KnowledgeGraphModelConfig():

    # def __init__(
    #     self,
    #     create_ontology: KnowledgeGraphModelStepConfig | None = None,
    #     extract_data: KnowledgeGraphModelStepConfig | None = None,
    #     cypher_generation: KnowledgeGraphModelStepConfig | None = None,
    #     qa: KnowledgeGraphModelStepConfig | None = None,
    # ):
    #     self.create_ontology = create_ontology
    #     self.extract_data = extract_data
    #     self.cypher_generation = cypher_generation
    #     self.qa = qa

    def __init__(self, d: dict):
        model = d.get("model")
        generation_config = d.get("generation_config")
        self.create_ontology = KnowledgeGraphModelStepConfig(
            model=model, generation_config=generation_config
        )
        self.extract_data = KnowledgeGraphModelStepConfig(
            model=model, generation_config=generation_config
        )
        self.cypher_generation = KnowledgeGraphModelStepConfig(
            model=model, generation_config=generation_config
        )
        self.qa = KnowledgeGraphModelStepConfig(
            model=model, generation_config=generation_config
        )
