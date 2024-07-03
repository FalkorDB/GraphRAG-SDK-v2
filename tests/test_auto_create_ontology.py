from dotenv import load_dotenv
load_dotenv()
from falkordb_gemini_kg.classes.ontology import Ontology
import unittest
from falkordb_gemini_kg.classes.source import Source
from falkordb_gemini_kg.models.gemini import GeminiGenerativeModel
import vertexai
import os
import logging

logging.basicConfig(level=logging.DEBUG)

vertexai.init(project=os.getenv("PROJECT_ID"), location=os.getenv("REGION"))


class TestAutoDetectOntology(unittest.TestCase):
    """
    Test auto-detect ontology
    """

    def test_auto_detect_ontology(self):

        file_path = "tests/data/madoff.txt"

        sources = [Source(file_path)]

        model = GeminiGenerativeModel(model_name="gemini-1.5-flash-001")

        boundaries = """
  Extract entities and relationships from each page
"""
        ontology = Ontology.from_sources(sources, boundaries=boundaries, model=model)

        logging.info(f"Ontology: {ontology.to_json()}")
