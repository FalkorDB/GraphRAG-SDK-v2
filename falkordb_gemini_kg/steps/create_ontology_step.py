from falkordb_gemini_kg.steps.Step import Step
from falkordb_gemini_kg.classes.source import AbstractSource
from concurrent.futures import Future, ThreadPoolExecutor, wait
from falkordb_gemini_kg.classes.ontology import Ontology
from falkordb_gemini_kg.classes.model_config import StepModelConfig
from vertexai.generative_models import GenerativeModel, ChatSession
from falkordb_gemini_kg.fixtures.prompts import (
    CREATE_ONTOLOGY_SYSTEM,
    CREATE_ONTOLOGY_PROMPT,
    FIX_ONTOLOGY_PROMPT,
)
import logging
from falkordb_gemini_kg.helpers import extract_json

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class CreateOntologyStep(Step):
    """
    Create Ontology Step
    """

    def __init__(
        self,
        sources: list[AbstractSource],
        ontology: Ontology,
        model_config: StepModelConfig,
        config: dict = {
            "max_workers": 16,
            "max_input_tokens": 500000,
            "max_output_tokens": 8192,
        },
    ) -> None:
        self.sources = sources
        self.ontology = ontology
        self.config = config
        self.chat_session = GenerativeModel(
            model_config.model,
            generation_config=model_config.generation_config.to_generation_config() if model_config.generation_config is not None else None,
            system_instruction=CREATE_ONTOLOGY_SYSTEM,
        ).start_chat()

    def run(self, boundaries: str):
        tasks: list[Future[Ontology]] = []
        with ThreadPoolExecutor(max_workers=self.config["max_workers"]) as executor:
            # extract entities and relationships from each page
            for source in self.sources:
                task = executor.submit(
                    self._process_source,
                    self.chat_session,
                    source,
                    self.ontology,
                    boundaries,
                )
                tasks.append(task)

            # Wait for all tasks to complete
            wait(tasks)

        for task in tasks:
            self.ontology = self.ontology.merge_with(task.result())

        self.ontology = self._fix_ontology(self.chat_session, self.ontology)

        return self.ontology

    def _process_source(
        self,
        chat_session: ChatSession,
        source: AbstractSource,
        o: Ontology,
        boundaries: str,
    ):
        text = next(source.load()).content[: self.config["max_input_tokens"]]

        user_message = CREATE_ONTOLOGY_PROMPT.format(text=text, boundaries=boundaries)

        model_response = chat_session.send_message(user_message)

        logger.debug(f"Model response: {model_response}")

        if (
            model_response.usage_metadata.candidates_token_count
            >= self.config["max_output_tokens"]
        ):
            # TODO: Handle this case
            raise Exception("Model response exceeds token limit")

        try:
            new_ontology = Ontology.from_json(extract_json(model_response.text))
        except Exception as e:
            logger.debug(f"Exception while extracting JSON: {e}")
            new_ontology = None

        if new_ontology is not None:
            o = o.merge_with(new_ontology)

        return o

    def _fix_ontology(self, chat_session: ChatSession, o: Ontology):
        logger.debug(f"Fixing ontology...")

        user_message = FIX_ONTOLOGY_PROMPT.format(ontology=o)

        model_response = chat_session.send_message(user_message)

        logger.debug(f"Model response: {model_response}")

        if (
            model_response.usage_metadata.candidates_token_count
            >= self.config["max_output_tokens"]
        ):
            # TODO: Handle this case
            raise Exception("Model response exceeds token limit")

        try:
            new_ontology = Ontology.from_json(extract_json(model_response.text))
        except Exception as e:
            print(f"Exception while extracting JSON: {e}")
            new_ontology = None

        if new_ontology is not None:
            o = o.merge_with(new_ontology)

        return o
