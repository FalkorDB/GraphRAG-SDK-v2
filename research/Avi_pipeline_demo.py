from llama_index.core import SimpleDirectoryReader, Document, Settings
from falkordb_gemini_kg.models.openai import OpenAiGenerativeModel
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from llama_index.llms.huggingface import HuggingFaceLLM
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

import nest_asyncio
import os
from llama_index.core import PropertyGraphIndex
from llama_index.extractors.relik.base import RelikPathExtractor


from llama_index.graph_stores.falkordb import FalkorDBPropertyGraphStore
from bs4 import BeautifulSoup
import os

class CustomSimpleDirectoryReader(SimpleDirectoryReader):
    def load_data(self):
        documents = []
        for file_name in os.listdir(self.input_dir):
            file_path = os.path.join(self.input_dir, file_name)
            with open(file_path, 'r', encoding='utf-8') as file:
                if file_name.endswith('.html'):
                    # Parse HTML file with BeautifulSoup
                    soup = BeautifulSoup(file, 'html.parser')
                    text = soup.get_text()
                elif file_name.endswith('.txt'):
                    # Directly read text file
                    text = file.read()
                else:
                    # Skip non .txt or .html files
                    continue
                
                # Create a Document object and append to the list
                document = Document(text=text, metadata={"file_name": file_name})
                documents.append(document)
        return documents

nest_asyncio.apply()
reader = CustomSimpleDirectoryReader(input_dir="research/data/")
documents = reader.load_data()
print(f"{documents[0]}")
print(f"{documents[1]}")

graph_store = FalkorDBPropertyGraphStore(
    url="falkor://localhost:6379",
)

print('start')
relik = RelikPathExtractor(
    model="relik-ie/relik-relation-extraction-small", model_config={"skip_metadata": True})
model = OpenAiGenerativeModel(model_name="gpt-4o")

Settings.llm = model
Settings.chunk_size = 512
index = PropertyGraphIndex.from_documents(
    documents,
    #embed_model=OpenAIEmbedding(model_name="text-embedding-3-small"),
    #embed_model=HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5"),
    kg_extractors=[relik],
    property_graph_store=graph_store,
    show_progress=True,
)
retriever = index.as_retriever(
    include_text=False,  # include source text in returned nodes, default True
)

nodes = retriever.retrieve("What is Intel?")
#nodes = retriever.retrieve("What happened at Interleaf and Viaweb?")

for node in nodes:
    print(node.text)
    
print('finish')
