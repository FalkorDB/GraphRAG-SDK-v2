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

Make sure that a `.env` file is present and contains all required credentials.

   <details>
     <summary>.env</summary>
  
   ```
   OPENAI_API_KEY="OPENAI_API_KEY"
   GOOGLE_API_KEY="GOOGLE_API_KEY"

   ```
  
   </details>

## Basic Usage

Here are instructions on how to utilize the powerful tools available in the GraphRAG SDK.

### Import source data
This SDK support the following file formats:

- PDF
- txt
- json
- URL
- HTML
- CSV

```python
import os
from graphrag_sdk.classes.source import Source

src_files = "Your data folder"
sources = []

# For each file in the source directory, create a new Source object
for file in os.listdir(src_files):
    sources.append(Source(os.path.join(src_files, file)))
```
### Ontology
You can choose either the Ontology is outdetect from your data or to preset it.
In addition you can set 'Boundaries' to the Ontolegy outodetection.


```python

from falkordb import FalkorDB
from graphrag_sdk import KnowledgeGraph, Ontology
from graphrag_sdk.models.openai import OpenAiGenerativeModel

AUTODETECTION_PRECENTAGE = 0.1
boundaries = """
    Extract only the most information about the fighters, fights, and events in the UFC.
    Do not create entities for what can be expressed as attributes.
"""

# use GeminiGenerativeModel for google models.
model = OpenAiGenerativeModel(model_name="gpt-4o")

# use only 10% from the files to auto detect the ontology.
ontology = Ontology.from_sources(
    sources=sources[: round(len(sources) * AUTODETECTION_PRECENTAGE)],
    boundaries=boundaries,
    model=model,
)


# TODO change is to repo kg
db = FalkorDB()
graph = db.select_graph("ufc_ontology")
ontology.save_to_graph(graph)

# Save ontology to json file
with open("YOUR_PROJECT_ontology.json", "w", encoding="utf-8") as file:
    file.write(json.dumps(ontology.to_json(), indent=2))
```
Now you can review your Ontology and update it whenever you see its right.
