from .ontology import Ontology
from .source import Source
from .node import Node
from .edge import Edge

# Setup Null handler
import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
