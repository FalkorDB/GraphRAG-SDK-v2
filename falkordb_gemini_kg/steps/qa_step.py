from falkordb_gemini_kg.steps.Step import Step
from falkordb_gemini_kg.classes.Document import Document
from falkordb_gemini_kg.classes.ontology import Ontology
from falkordb_gemini_kg.classes.model_config import StepModelConfig
from vertexai.generative_models import GenerativeModel, ChatSession
from falkordb_gemini_kg.fixtures.prompts import GRAPH_QA_SYSTEM, GRAPH_QA_PROMPT
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class QAStep(Step):
    """
    QA Step
    """

    def __init__(
        self,
        model_config: StepModelConfig | None = None,
        config: dict = {},
        chat_session: ChatSession | None = None,
    ) -> None:
        assert chat_session is not None or (
            model_config is not None
        ), "Must provide either a chat session or model config"
        self.config = config
        self.chat_session = (
            chat_session
            or GenerativeModel(
                model_config.model,
                generation_config=(
                    model_config.generation_config.to_generation_config()
                    if model_config.generation_config is not None
                    else None
                ),
                system_instruction=GRAPH_QA_SYSTEM,
            ).start_chat()
        )

    def run(self, question: str, cypher: str, context: str):

        qa_prompt = GRAPH_QA_PROMPT.format(
            context=context, cypher=cypher, question=question
        )

        # logger.debug(f"QA Prompt: {qa_prompt}")
        qa_response = self.chat_session.send_message(qa_prompt)

        return qa_response.text
