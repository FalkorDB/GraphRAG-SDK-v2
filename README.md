> [!IMPORTANT]
> **GraphRAG-SDK-V2 is in development and is actively changing.**
>
> This version is expected to succeed [GraphRAG-SDK](https://github.com/FalkorDB/GraphRAG-SDK) in the near future.
> 
> We greatly appreciate the community's feedback and support.

[![Dockerhub](https://img.shields.io/docker/pulls/falkordb/falkordb?label=Docker)](https://hub.docker.com/r/falkordb/falkordb/)
[![Discord](https://img.shields.io/discord/1146782921294884966?style=flat-square)](https://discord.gg/6M4QwDXn2w)

# GraphRAG-SDK-V2
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
from graphrag_sdk.classes.model_config import KnowledgeGraphModelConfig
from graphrag_sdk.models.openai import OpenAiGenerativeModel
from graphrag_sdk import KnowledgeGraph, Ontology
from graphrag_sdk.classes.source import URL
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

## Multi Agent
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/FalkorDB/GraphRAG-SDK-v2/blob/master/examples/trup/demo_orchestrator_trip.ipynb)


The following example demonstrates how to use the FalkorDB GraphRAG SDK to create a multi-agent query system.

```python
from dotenv import load_dotenv
from graphrag_sdk import (
    Ontology, Entity, Relation, Attribute, AttributeType, KnowledgeGraph, KnowledgeGraphModelConfig
)
from graphrag_sdk.orchestrator import Orchestrator
from graphrag_sdk.agents.kg_agent import KGAgent
from graphrag_sdk.models.openai import OpenAiGenerativeModel
from json import loads
import os
import vertexai

# Load environment variables
load_dotenv()

# Initialize the Vertex AI client
vertexai.init(project=os.getenv("PROJECT_ID"), location=os.getenv("REGION"))
```
### Reads data from JSON files into two Knowledge Graphs, representing multi-agent entities and their relationships.
```python
def import_data():
        with open("data/cities.json") as f:
            cities = loads(f.read())
        with open("data/restaurants.json") as f:
            restaurants = loads(f.read())
        with open("data/attractions.json") as f:
            attractions = loads(f.read())

        for city in cities:
            restaurants_kg.add_node(
                "City",
                {
                    "name": city["name"],
                    "weather": city["weather"],
                    "population": city["population"],
                },
            )
            restaurants_kg.add_node("Country", {"name": city["country"]})
            restaurants_kg.add_edge(
                "IN_COUNTRY",
                "City",
                "Country",
                {"name": city["name"]},
                {"name": city["country"]},
            )

            attractions_kg.add_node(
                "City",
                {
                    "name": city["name"],
                    "weather": city["weather"],
                    "population": city["population"],
                },
            )
            attractions_kg.add_node("Country", {"name": city["country"]})
            attractions_kg.add_edge(
                "IN_COUNTRY",
                "City",
                "Country",
                {"name": city["name"]},
                {"name": city["country"]},
            )

        for restaurant in restaurants:
            restaurants_kg.add_node(
                "Restaurant",
                {
                    "name": restaurant["name"],
                    "description": restaurant["description"],
                    "rating": restaurant["rating"],
                    "food_type": restaurant["food_type"],
                },
            )
            restaurants_kg.add_edge(
                "IN_CITY",
                "Restaurant",
                "City",
                {"name": restaurant["name"]},
                {"name": restaurant["city"]},
            )

        for attraction in attractions:
            attractions_kg.add_node(
                "Attraction",
                {
                    "name": attraction["name"],
                    "description": attraction["description"],
                    "type": attraction["type"],
                },
            )
            attractions_kg.add_edge(
                "IN_CITY",
                "Attraction",
                "City",
                {"name": attraction["name"]},
                {"name": attraction["city"]},
            )
```
### Add Ontology
```python

restaurants_ontology = Ontology()
attractions_ontology = Ontology()
restaurants_ontology.add_entity(
    Entity(
        label="Country",
        attributes=[
            Attribute(
                name="name",
                attr_type=AttributeType.STRING,
                required=True,
                unique=True,
            ),
        ],
    )
)
restaurants_ontology.add_entity(
    Entity(
        label="City",
        attributes=[
            Attribute(
                name="name",
                attr_type=AttributeType.STRING,
                required=True,
                unique=True,
            ),
            Attribute(
                name="weather",
                attr_type=AttributeType.STRING,
                required=False,
                unique=False,
            ),
            Attribute(
                name="population",
                attr_type=AttributeType.NUMBER,
                required=False,
                unique=False,
            ),
        ],
    )
)
restaurants_ontology.add_entity(
    Entity(
        label="Restaurant",
        attributes=[
            Attribute(
                name="name",
                attr_type=AttributeType.STRING,
                required=True,
                unique=True,
            ),
            Attribute(
                name="description",
                attr_type=AttributeType.STRING,
                required=False,
                unique=False,
            ),
            Attribute(
                name="rating",
                attr_type=AttributeType.NUMBER,
                required=False,
                unique=False,
            ),
            Attribute(
                name="food_type",
                attr_type=AttributeType.STRING,
                required=False,
                unique=False,
            ),
        ],
    )
)
restaurants_ontology.add_relation(
    Relation(
        label="IN_COUNTRY",
        source="City",
        target="Country",
    )
)
restaurants_ontology.add_relation(
    Relation(
        label="IN_CITY",
        source="Restaurant",
        target="City",
    )
)

attractions_ontology.add_entity(
    Entity(
        label="Country",
        attributes=[
            Attribute(
                name="name",
                attr_type=AttributeType.STRING,
                required=True,
                unique=True,
            ),
        ],
    )
)
attractions_ontology.add_entity(
    Entity(
        label="City",
        attributes=[
            Attribute(
                name="name",
                attr_type=AttributeType.STRING,
                required=True,
                unique=True,
            ),
            Attribute(
                name="weather",
                attr_type=AttributeType.STRING,
                required=False,
                unique=False,
            ),
            Attribute(
                name="population",
                attr_type=AttributeType.NUMBER,
                required=False,
                unique=False,
            ),
        ],
    )
)
attractions_ontology.add_entity(
    Entity(
        label="Attraction",
        attributes=[
            Attribute(
                name="name",
                attr_type=AttributeType.STRING,
                required=True,
                unique=True,
            ),
            Attribute(
                name="description",
                attr_type=AttributeType.STRING,
                required=False,
                unique=False,
            ),
            Attribute(
                name="type",
                attr_type=AttributeType.STRING,
                required=False,
                unique=False,
            ),
        ],
    )
)
attractions_ontology.add_relation(
    Relation(
        label="IN_COUNTRY",
        source="City",
        target="Country",
    )
)
attractions_ontology.add_relation(
    Relation(
        label="IN_CITY",
        source="Attraction",
        target="City",
    )
)
```
### Multi-agent objects.

```python
# Create Knowledge Graphs
model = OpenAiGenerativeModel("gpt-4o")
restaurants_kg = KnowledgeGraph(
    name="restaurants",
    ontology=restaurants_ontology,
    model_config=KnowledgeGraphModelConfig.with_model(model),
)
attractions_kg = KnowledgeGraph(
    name="attractions",
    ontology=attractions_ontology,
    model_config=KnowledgeGraphModelConfig.with_model(model),
)

# Import data into Knowledge Graphs
import_data()

# Setup multi-agent system
restaurants_agent = KGAgent(
    agent_id="restaurants_agent",
    kg=restaurants_kg,
    introduction="I'm a restaurant agent, specialized in finding the best restaurants for you.",
)

attractions_agent = KGAgent(
    agent_id="attractions_agent",
    kg=attractions_kg,
    introduction="I'm an attractions agent, specialized in finding the best attractions for you.",
)
```
### Orchestrator and multi-agent questioning
```python
# Initialize the orchestrator and register agents
orchestrator = Orchestrator(
    model,
    backstory="You are a trip planner, and you want to provide the best possible itinerary for your clients.",
)
orchestrator.register_agent(restaurants_agent)
orchestrator.register_agent(attractions_agent)

# Query the orchestrator
runner = orchestrator.ask("Write me a 2 day itinerary for a trip to Italy. Do not ask any questions to me, just provide your best itinerary.")

print(runner.output)
```
```
Thank you for your patience! Based on the information gathered from the agents, here is a detailed 2-day itinerary for your trip to Italy:

### Day 1: Rome
**Morning:**
1. **Colosseum**: Start your day early with a visit to the iconic Colosseum. One of Italy’s most enduring attractions, it’s a must-see for any visitor. Allocate about 2-3 hours here.
2. **Roman Forum and Palatine Hill**: Just a short walk from the Colosseum, explore the historical ruins which were the center of ancient Rome. Spend around 2 hours here.

**Lunch:**
- **Il Pagliaccio**: Located in the heart of Rome, this Michelin-starred restaurant offers contemporary Italian cuisine. Perfect for a luxurious and memorable dining experience. 

**Afternoon:**
1. **Pantheon**: After lunch, head to the Pantheon, one of the best-preserved monuments of ancient Rome. Spend approximately an hour here.
2. **Trevi Fountain**: Take a leisurely walk to the Trevi Fountain. Don’t forget to toss a coin into the fountain for good luck. Spend some time taking in the beauty and capturing photographs.
3. **Piazza Navona**: End your afternoon with a visit to the vibrant and lively Piazza Navona.

**Dinner:**
- Enjoy a typical Roman dinner at a local trattoria near your hotel or explore other fine dining options in the area.

### Day 2: Florence
**Morning:**
1. **Duomo di Firenze (Florence Cathedral)**: Start your day with a visit to this stunning cathedral. Don't miss the chance to climb to the dome for panoramic views of the city. Allocate about 1.5-2 hours.
2. **Uffizi Gallery**: Spend your late morning marveling at the Renaissance masterpieces housed in one of the world's most famous art museums. Plan for around 2-3 hours here.

**Lunch:**
- **La Bottega del Buon Caffè**: This upscale restaurant offers seasonal Tuscan cuisine with a modern twist, making it a perfect spot for a delightful lunch.
...
**Dinner:**
- Find a cozy restaurant in Florence’s historic center to savor some traditional Florentine dishes as you reflect on your day.

This itinerary balances historical landmarks with fine dining, ensuring you get a comprehensive taste of Italy's rich culture, history, and cuisine in just two days. Enjoy your trip!
```