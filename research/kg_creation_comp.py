import os
import json
import vertexai
from random import shuffle
from falkordb import FalkorDB
from dotenv import load_dotenv
from falkordb_gemini_kg.classes.source import TEXT
from falkordb_gemini_kg import KnowledgeGraph, Ontology
from falkordb_gemini_kg.models.openai import OpenAiGenerativeModel
from falkordb_gemini_kg.classes.model_config import KnowledgeGraphModelConfig
os.environ['OPENAI_API_KEY'] = 'sk-proj-5lxkQXgxTkiQDBnQNTFhT3BlbkFJn9wCDMrokYKcLDqsGUSx'
load_dotenv()
from llama_index.core import StorageContext
from llama_index.core import PropertyGraphIndex
from llama_index.core import Settings
from llama_index.core import Document
from llama_index.extractors.relik.base import RelikPathExtractor
from llama_index.embeddings.openai import OpenAIEmbedding

from llama_index.llms.openai import OpenAI
from llama_index.graph_stores.falkordb import FalkorDBGraphStore
from llama_index.core import SimpleDirectoryReader, KnowledgeGraphIndex

import requests
from bs4 import BeautifulSoup
t = """
    Throughout the history of football, several players have set remarkable records for goal-scoring, leaving an indelible mark on the sport. Cristiano Ronaldo has scored over 850 goals throughout his career, showcasing his talent across several teams: Sporting CP (5 goals in 31 appearances), Manchester United (145 goals in 346 appearances), Real Madrid (450 goals in 438 appearances), Juventus (101 goals in 134 appearances), and Al-Nassr (10 goals in 14 appearances).

Lionel Messi follows closely with over 820 goals, demonstrating his exceptional skill with FC Barcelona (672 goals in 778 appearances), Paris Saint-Germain (32 goals in 75 appearances), and Inter Miami (15 goals in 24 appearances).

Pele, a football legend, has netted more than 770 goals, notably at Santos (643 goals in 656 appearances) and New York Cosmos (36 goals in 64 appearances), among other clubs.

Josef Bican, known for his prolific scoring, accumulated over 760 goals, primarily with Slovan Bratislava (159 goals in 150 appearances) and Rapid Vienna (357 goals in 217 appearances).

Lastly, Romario, with over 750 goals, made significant contributions at clubs such as Vasco da Gama (71 goals in 106 appearances), Barcelona (39 goals in 65 appearances), and various Brazilian teams throughout his career.
"""
def fetch_wikipedia_page(title):
    url = f"https://en.wikipedia.org/wiki/{title}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup.get_text()

source = [TEXT(fetch_wikipedia_page("List_of_men%27s_footballers_with_1,000_or_more_official_appearances"))]

source = [TEXT(t)]

boundaries = """"""
#     Extract only footballers and their teams, appearances and goals.
#     Do not create entities for what can be expressed as attributes.
# """

db = FalkorDB()
model = OpenAiGenerativeModel(model_name="gpt-4o")

ontology = Ontology.from_sources(
    sources=source,
    boundaries=boundaries,
    model=model,
)
graph = db.select_graph("footballers_ontology_1")
ontology.save_to_graph(graph)

kg = KnowledgeGraph(
    name="footballers_1",
    model_config=KnowledgeGraphModelConfig.with_model(model),
    ontology=ontology,
)
kg.process_sources(source)

print(kg.ask("how much teams Peter Shilton played"))
print(kg.ask("what can you tell me about messi?"))

ontology_ent = [en.label for en in ontology.entities]
ontology_rel = [en.label for en in ontology.relations]

graph_store = FalkorDBGraphStore(
    "redis://localhost:6379", decode_responses=True
)
storage_context = StorageContext.from_defaults(graph_store=graph_store)
relik = RelikPathExtractor(
    model="relik-ie/relik-relation-extraction-small", model_config={"skip_metadata": True})
Settings.llm = model
Settings.chunk_size = 512
documents = [
    Document(text=t)
]
index = PropertyGraphIndex.from_documents(
    documents,
    kg_extractors=[relik],
    storage_context=storage_context,
    show_progress=True
)

query_engine = index.as_query_engine(include_text=True)

query_engine.query("how much teams Messi played?")

from relik import Relik
from relik.inference.data.objects import RelikOutput
from relik.retriever.indexers.inmemory import InMemoryDocumentIndex
relik = Relik.from_pretrained("sapienzanlp/relik-entity-linking-small")
wikidata_index = InMemoryDocumentIndex.from_pretrained("relik-ie/encoder-e5-small-v2-wikipedia-relations-index", index_precision="bf16")
