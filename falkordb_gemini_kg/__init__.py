from .classes.source import Source
from .classes.ontology import Ontology
from .kg import KnowledgeGraph
from .classes.model_config import KnowledgeGraphModelConfig, StepModelConfig
from .steps.create_ontology_step import CreateOntologyStep

# Setup Null handler
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.NullHandler())
