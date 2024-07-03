from falkordb_gemini_kg.models import GenerativeModel


class KnowledgeGraphModelConfig:

    def __init__(
        self,
        extract_data: GenerativeModel,
        cypher_generation: GenerativeModel,
        qa: GenerativeModel,
    ):
        self.extract_data = extract_data
        self.cypher_generation = cypher_generation
        self.qa = qa

    @staticmethod
    def with_model(model: GenerativeModel):
        return KnowledgeGraphModelConfig(
            extract_data=model,
            cypher_generation=model,
            qa=model,
        )
