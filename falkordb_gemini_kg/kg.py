import logging
from falkordb_gemini_kg.classes.ontology import Ontology
from falkordb import FalkorDB
from falkordb_gemini_kg.classes.source import AbstractSource
from falkordb_gemini_kg.classes.model_config import KnowledgeGraphModelConfig
from falkordb_gemini_kg.steps.extract_data_step import ExtractDataStep
from falkordb_gemini_kg.steps.graph_query_step import GraphQueryGenerationStep
from falkordb_gemini_kg.fixtures.prompts import GRAPH_QA_SYSTEM, CYPHER_GEN_SYSTEM
from falkordb_gemini_kg.steps.qa_step import QAStep
from falkordb_gemini_kg.classes.ChatSession import ChatSession

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class KnowledgeGraph:
    """Knowledge Graph model data as a network of entities and relations
    To create one it is best to provide a ontology which will define the graph's ontology
    In addition to a set of sources from which entities and relations will be extracted.
    """

    def __init__(
        self,
        name: str,
        model_config: KnowledgeGraphModelConfig,
        ontology: Ontology,
        host: str = "127.0.0.1",
        port: int = 6379,
        username: str | None = None,
        password: str | None = None,
    ):
        """
        Initialize Knowledge Graph

        Parameters:
            name (str): Knowledge graph name.
            model (GenerativeModel): The Google GenerativeModel to use.
            host (str): FalkorDB hostname.
            port (int): FalkorDB port number.
            username (str|None): FalkorDB username.
            password (str|None): FalkorDB password.
            ontology (Ontology|None): Ontology to use.
        """

        if not isinstance(name, str) or name == "":
            raise Exception("name should be a non empty string")

        # connect to database
        self.db = FalkorDB(host=host, port=port, username=username, password=password)
        self.graph = self.db.select_graph(name)

        self._name = name
        self._ontology = ontology
        self._model_config = model_config
        self.sources = set([])

    # Attributes

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        raise AttributeError("Cannot modify the 'name' attribute")

    @property
    def ontology(self):
        return self._ontology

    @ontology.setter
    def ontology(self, value):
        self._ontology = value

    def list_sources(self) -> list[AbstractSource]:
        """
        List of sources associated with knowledge graph

        Returns:
            list[AbstractSource]: sources
        """

        return [s.source for s in self.sources]

    def process_sources(self, sources: list[AbstractSource]) -> None:
        """
        Add entities and relations found in sources into the knowledge-graph

        Parameters:
            sources (list[AbstractSource]): list of sources to extract knowledge from
        """

        if self.ontology is None:
            raise Exception("Ontology is not defined")

        # Create graph with sources
        self._create_graph_with_sources(sources)

        # Add processed sources
        for src in sources:
            self.sources.add(src)

    def _create_graph_with_sources(self, sources: list[AbstractSource] | None = None):

        step = ExtractDataStep(
            sources=list(sources),
            ontology=self.ontology,
            model=self._model_config.extract_data,
            graph=self.graph,
        )

        step.run()

    def ask(self, question: str) -> str:
        """
        Query the knowledge graph using natural language
        if the query is asked as part of a longer conversation make sure to
        include past history.

        Returns:
            str: answer

         Example:
            >>> ans = kg.ask("Which actor has the most oscars")
            >>> ans = kg.ask("List a few movies in which that actored played in", history)
        """

        cypher_chat_session = (
            self._model_config.cypher_generation.with_system_instruction(
                CYPHER_GEN_SYSTEM.replace("#ONTOLOGY", str(self.ontology.to_json())),
            ).start_chat()
        )
        cypher_step = GraphQueryGenerationStep(
            ontology=self.ontology,
            chat_session=cypher_chat_session,
            graph=self.graph,
        )

        (context, cypher) = cypher_step.run(question)

        qa_chat_session = self._model_config.qa.with_system_instruction(
            GRAPH_QA_SYSTEM
        ).start_chat()
        qa_step = QAStep(
            chat_session=qa_chat_session,
        )

        answer = qa_step.run(question, cypher, context)

        return answer

    def delete(self) -> None:
        """
        Deletes the knowledge graph and any other related resource
        e.g. Ontology, data graphs
        """
        # List available graphs
        available_graphs = self.db.list_graphs()

        # Delete KnowledgeGraph
        if self.name in available_graphs:
            self.graph.delete()

        # Nullify all attributes
        for key in self.__dict__.keys():
            setattr(self, key, None)

    def chat_session(self) -> ChatSession:
        return ChatSession(self._model_config, self.ontology, self.graph)
