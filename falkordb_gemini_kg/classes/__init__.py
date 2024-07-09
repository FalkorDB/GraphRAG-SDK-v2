from .ontology import Ontology
from .source import Source
from .entity import Entity
from .relation import Relation
from .attribute import Attribute, AttributeType

# Setup Null handler
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
