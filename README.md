[![Dockerhub](https://img.shields.io/docker/pulls/falkordb/falkordb?label=Docker)](https://hub.docker.com/r/falkordb/falkordb/)
[![Discord](https://img.shields.io/discord/1146782921294884966?style=flat-square)](https://discord.gg/6M4QwDXn2w)

# GraphRAG-SDK
[![Try Free](https://img.shields.io/badge/Try%20Free-FalkorDB%20Cloud-FF8101?labelColor=FDE900&style=for-the-badge&link=https://app.falkordb.cloud)](https://app.falkordb.cloud)

GraphRAG-SDK-v2 is designed to facilitate the creation of a Graph Retrieval-Augmented Generation (GraphRAG) solutions. Built on top of FalkorDB, it offers seamless integration with different LLMs (OpenAI, Gemini...) to enable advanced multi agent data querying and Multi knowledge graph construction.

## Features

* Schema Management: Define and manage data schemas either manually or automatically from unstructured data.
* Knowledge Graph: Construct and query knowledge graphs for efficient data retrieval.
* LLMs Integration: Enhance your RAG solutions with AI-driven insights.

## Install

```sh
pip install git+https://github.com/FalkorDB/GraphRAG-SDK-v2.git
```

## Example

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/FalkorDB/GraphRAG-SDK-v2/blob/master/examples/movies/demo-movies.ipynb)


### Prerequisites
GraphRAG-SDK-v2 relies on [FalkorDB](http://falkordb.com) as its graph engine and works with OpenAI/Gemini.

Start FalkorDB locally:

```sh
docker run -p 6379:6379 -it --rm -v ./data:/data falkordb/falkordb
```

Export your OpenAI API KEY:

```sh
export OPENAI_API_KEY=<YOUR_OPENAI_KEY>
```

```python
from graphrag_sdk.schema import Schema
from graphrag_sdk import KnowledgeGraph, Source

# Auto generate graph schema from unstructured data
sources = [Source("./data/the_matrix.txt")]
s = Schema.auto_detect(sources)

# Create a knowledge graph based on schema
g = KnowledgeGraph("IMDB", schema=s)
g.process_sources(sources)

# Query your data
question = "Name a few actors who've played in 'The Matrix'"
answer, messages = g.ask(question)
print(f"Answer: {answer}")

# Output:
# Answer: A few actors who've played in 'The Matrix' are:
# - Keanu Reeves
# - Laurence Fishburne
# - Carrie-Anne Moss
# - Hugo Weaving
```

## Introduction

GraphRAG-SDK provides easy-to-use tooling to get you up and running with your own
Graph-RAG solution.

There are two main components:

### Schema

A `schema` represents the types of entities and relationships within your data.
For example, the main entities in your data are:  Movies, Actors, and Directors.
These are interconnected via `ACT` and `DIRECTED` edges.


```python
from dotenv import load_dotenv

load_dotenv()
from falkordb_gemini_kg.classes.model_config import KnowledgeGraphModelConfig
from falkordb_gemini_kg.models.openai import OpenAiGenerativeModel
from falkordb_gemini_kg import KnowledgeGraph, Ontology
from falkordb_gemini_kg.classes.source import URL
import vertexai
import os
from random import shuffle
import json
from falkordb import FalkorDB

# Initialize the Vertex AI client
vertexai.init(project=os.getenv("PROJECT_ID"), location=os.getenv("REGION"))
```

### Import source data

```
src_file="../data/movies/rottentomatoes.txt"

source_urls = []
with open(src_file, "r", encoding="utf-8") as file:
    source_urls = file.readlines()

shuffle(source_urls)

sources = [URL(url) for url in source_urls]

model = OpenAiGenerativeModel(model_name="gpt-4o")
```

### Automatically create the ontology from 20% of the sources

```python
boundaries = "Extract all information related to the movies. The graph does not need to contain data about the plot of the movie, but everything else related to it."

ontology = Ontology.from_sources(
    sources=sources[: round(len(sources) * 0.2)],
    boundaries=boundaries,
    model=model,
)


db = FalkorDB()
graph = db.select_graph("movies_ontology")
ontology.save_to_graph(graph)

# Save ontology to json file
with open("ontology_n.json", "w", encoding="utf-8") as file:
    file.write(json.dumps(ontology.to_json(), indent=2))
```

### Read ontology from json file

```python
ontology_file = "ontology.json"
with open(ontology_file, "r", encoding="utf-8") as file:
    ontology = Ontology.from_json(json.loads(file.read()))

kg = KnowledgeGraph(
    name="movies",
    model_config=KnowledgeGraphModelConfig.with_model(model),
    ontology=ontology,
)
```

### Process the sources raw data into the knowledge graph

```python
kg.process_sources(sources)

Relation with label MENTIONED not found in ontology

Ask a single question to the model

kg.ask("How are Keanu Reeves and Carrie-Anne Moss related?")

'Keanu Reeves and Carrie-Anne Moss have acted in the same movies, "The Matrix" and "The Matrix Reloaded." \n'

Start a chat session with the model

chat = kg.chat_session()

print(chat.send_message("Who is the director of the movie The Matrix?"))
print(chat.send_message("And how are they related with Keanu Reeves?"))
```

Lana Wachowski and Lilly Wachowski directed the movie The Matrix. 

Lana Wachowski and Lilly Wachowski directed the movie The Matrix, in which Keanu Reeves acted. 


