from abc import ABC, abstractmethod


class FinishReason:
    MAX_TOKENS = "MAX_TOKENS"
    STOP = "STOP"
    OTHER = "OTHER"


class GenerativeModelConfig:
    def __init__(
        self,
        temperature: float,
        top_p: float,
        top_k: int,
        max_output_tokens: int,
        stop_sequences: list[str],
    ):
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.max_output_tokens = max_output_tokens
        self.stop_sequences = stop_sequences


class GenerationResponse:

    def __init__(self, text: str, finish_reason: FinishReason):
        self.text = text
        self.finish_reason = finish_reason

    def __str__(self) -> str:
        return f"GenerationResponse(text={self.text}, finish_reason={self.finish_reason})"


class GenerativeModelChatSession(ABC):

    @abstractmethod
    def __init__(self, model: "GenerativeModel"):
        self.model = model

    @abstractmethod
    def send_message(self, message: str) -> GenerationResponse:
        pass


class GenerativeModel(ABC):

    @abstractmethod
    def with_system_instruction(self, system_instruction: str) -> "GenerativeModel":
        pass

    @abstractmethod
    def start_chat(self, args: dict | None) -> GenerativeModelChatSession:
        pass

    @abstractmethod
    def ask(self, message: str) -> GenerationResponse:
        pass
