import json
from falkordb_gemini_kg.fixtures.regex import *
import logging

logger = logging.getLogger(__name__)


class AttributeType:
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"

    @staticmethod
    def fromString(txt: str):
        if txt.isdigit():
            return AttributeType.NUMBER
        elif txt.lower() in ["true", "false"]:
            return AttributeType.BOOLEAN
        return AttributeType.STRING


class Attribute:
    def __init__(
        self, name: str, attr_type: AttributeType, unique: bool, required: bool = False
    ):
        self.name = name
        self.type = attr_type
        self.unique = unique
        self.required = required

    @staticmethod
    def from_json(txt: str):
        txt = txt if isinstance(txt, dict) else json.loads(txt)
        if txt["type"] not in [
            AttributeType.STRING,
            AttributeType.NUMBER,
            AttributeType.BOOLEAN,
        ]:
            raise Exception(f"Invalid attribute type: {txt['type']}")
        return Attribute(
            txt["name"],
            txt["type"],
            txt["unique"],
            txt["required"] if "required" in txt else False,
        )

    @staticmethod
    def from_string(txt: str):
        name = txt.split(":")[0].strip()
        attr_type = txt.split(":")[1].split("!")[0].split("*")[0].strip()
        unique = "!" in txt
        required = "*" in txt

        if attr_type not in [
            AttributeType.STRING,
            AttributeType.NUMBER,
            AttributeType.BOOLEAN,
        ]:
            raise Exception(f"Invalid attribute type: {attr_type}")

        return Attribute(name, attr_type, unique, required)

    def to_json(self):
        return {
            "name": self.name,
            "type": self.type,
            "unique": self.unique,
            "required": self.required,
        }

    def __str__(self) -> str:
        return f"{self.name}: \"{self.type}{'!' if self.unique else ''}{'*' if self.required else ''}\""

