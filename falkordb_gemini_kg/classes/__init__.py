from .ontology import Ontology
from .source import Source
from .node import Node
from .edge import Edge
from .attribute import Attribute, AttributeType

# Setup Null handler
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
