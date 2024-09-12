# GraphRAG-SDK-V2
[![Try Free](https://img.shields.io/badge/Try%20Free-FalkorDB%20Cloud-FF8101?labelColor=FDE900&style=for-the-badge&link=https://app.falkordb.cloud)](https://app.falkordb.cloud)
[![Dockerhub](https://img.shields.io/docker/pulls/falkordb/falkordb?label=Docker)](https://hub.docker.com/r/falkordb/falkordb/)
[![Discord](https://img.shields.io/discord/1146782921294884966?style=flat-square)](https://discord.gg/6M4QwDXn2w)


GraphRAG-SDK is a comprehensive solution for building Graph Retrieval-Augmented Generation (GraphRAG) applications, leveraging [FalkorDB](https://www.falkordb.com/) for optimal performance. It offers powerful features including Ontology Management to define and manage data schemas from both structured and unstructured sources. Users can construct and query Knowledge Graphs (KG) for efficient data retrieval. The SDK also integrates with various LLMs, such as OpenAI and Gemini, and includes a Multi-Agent System to support the creation and management of multi-agent orchestrators with KG-based agents for smooth and effective collaboration.

## Features

* Ontology Management: Define and manage ontology (data schemas) either manually or automatically from unstructured data.
* Knowledge Graph (KG): Construct and query knowledge graphs for efficient data retrieval.
* LLMs Integration: Enhance your RAG solutions with AI-driven insights.
* Multi-Agent System: Implement and manage multi-agent orchestrators with KG-based agents and RAG integration for seamless collaboration.

## Get Started


### Install

```sh
pip install graphrag_sdk
```

### Prerequisites

#### Graph Database
GraphRAG-SDK relies on [FalkorDB](http://falkordb.com) as its graph engine and works with OpenAI/Gemini.

Use [FalkorDB Cloud](https://app.falkordb.cloud/) to get credentials or start FalkorDB locally:

```sh
docker run -p 6379:6379 -it --rm -v ./data:/data falkordb/falkordb
```
#### LLM Models
Currently, this SDK support the following LLMs API:

- [OpenAI](https://openai.com/index/openai-api) Recommended model:`gpt-4o`
- [google](https://makersuite.google.com/app/apikey) Recommended model:`gemini-1.5-flash-001`

Make sure that a `.env` file is present with all required credentials.

   <details>
     <summary>.env</summary>
  
   ```
   OPENAI_API_KEY="OPENAI_API_KEY"
   GOOGLE_API_KEY="GOOGLE_API_KEY"

   ```
  
   </details>

## Basic Usage
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/FalkorDB/GraphRAG-SDK-v2/blob/master/examples/ufc/demo-ufc.ipynb)

### Import source data
The SDK supports the following file formats:

- PDF
- txt
- json
- URL
- HTML
- CSV

```python
import os
from graphrag_sdk.classes.source import Source

src_files = "your_data_folder"
sources = []

# Create a Source object for each file in the source directory
for file in os.listdir(src_files):
    sources.append(Source(os.path.join(src_files, file)))
```
### Ontology
You can either auto-detect the ontology from your data or define it manually. Additionally, you can set `Boundaries` for ontology auto-detection.

Once the ontology is created, you can review, modify, and update it as needed before using it to build the Knowledge Graph (KG).

```python

from falkordb import FalkorDB
from graphrag_sdk import KnowledgeGraph, Ontology
from graphrag_sdk.models.openai import OpenAiGenerativeModel

AUTODETECTION_PERCENTAGE = 0.1
boundaries = """
    Extract only the most information about ---------.
    Do not create entities for what can be expressed as attributes.
"""

# use GeminiGenerativeModel for google models.
model = OpenAiGenerativeModel(model_name="gpt-4o")

# use only 10% from the files to auto detect the ontology.
ontology = Ontology.from_sources(
    sources=sources[: round(len(sources) * AUTODETECTION_PERCENTAGE)],
    boundaries=boundaries,
    model=model,
)


# TODO change is to repo kg
db = FalkorDB()
graph = db.select_graph("your_project_ontology")
ontology.save_to_graph(graph)

# Save ontology to json file
with open("your_project_ontology.json", "w", encoding="utf-8") as file:
    file.write(json.dumps(ontology.to_json(), indent=2))
```
YAfter generating the initial ontology, you can review it and make any necessary modifications to better fit your data and requirements. This might include refining entity types or adjusting relationships.

Once you are satisfied with the ontology, you can proceed to use it for creating and managing your Knowledge Graph (KG).

### Knowledge Graph
Now, you can use the SDK to create a Knowledge Graph (KG) from your sources and ontology.

```python
ontology_file = "your_project_ontology.json"
with open(ontology_file, "r", encoding="utf-8") as file:
    ontology = Ontology.from_json(json.loads(file.read()))

kg = KnowledgeGraph(
    name="your_project_name",
    model_config=KnowledgeGraphModelConfig.with_model(model),
    ontology=ontology,
)

kg.process_sources(sources)
```
You can update the KG at any time by processing more sources with the `process_sources` method.

### Graph RAG
At this point, you have a Knowledge Graph that can be queried using this SDK. You can use the `ask` method for single questions or `chat_session` for conversations.

```python
response = kg.ask("How are Keanu Reeves and Carrie-Anne Moss related?")

chat = kg.chat_session()
response = chat.send_message("Who is the director of the movie The Matrix?")
response = chat.send_message("And how are they related with Keanu Reeves?")
```

## Multi Agent - Orchestrator
The GraphRAG-SDK supports KG agents. Each agent uses GraphRAG based on your knowledge.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/FalkorDB/GraphRAG-SDK-v2/blob/master/examples/trip/demo_orchestrator_trip.ipynb)

### Agents
See the [Basic Usage](#Basic-Usage) section to create a KG object and use it as follows to create the agents.

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


# Setup agents
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

### Orchestrator - Multi-Agent System
The orchestrator manages the usage of agents and handles questioning.

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

```

## Support
Connect with our community for support and discussions. If you have any questions, don’t hesitate to contact us through one of the methods below:

- [Discord]()
- [Email](gal@falkordb.com)

