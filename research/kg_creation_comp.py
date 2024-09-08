import os
import json
import vertexai
from random import shuffle
from falkordb import FalkorDB
from dotenv import load_dotenv
from graphrag_sdk.classes.source import TEXT
from graphrag_sdk import KnowledgeGraph, Ontology
from graphrag_sdk.models.openai import OpenAiGenerativeModel
from graphrag_sdk.classes.model_config import KnowledgeGraphModelConfig

# from llama_index.core import StorageContext
# from llama_index.core import PropertyGraphIndex
# from llama_index.core import Settings
# from llama_index.core import Document
# from llama_index.extractors.relik.base import RelikPathExtractor
# from llama_index.embeddings.openai import OpenAIEmbedding

# from llama_index.llms.openai import OpenAI
# from llama_index.graph_stores.falkordb import FalkorDBGraphStore
# from llama_index.core import SimpleDirectoryReader, KnowledgeGraphIndex
load_dotenv()

import requests
from bs4 import BeautifulSoup


src_files = "../data/synthetic/"
t = """
    Throughout the history of football, several players have set remarkable records for goal-scoring, leaving an indelible mark on the sport. Cristiano Ronaldo has scored over 850 goals throughout his career, showcasing his talent across several teams: Sporting CP (5 goals in 31 appearances), Manchester United (145 goals in 346 appearances), Real Madrid (450 goals in 438 appearances), Juventus (101 goals in 134 appearances), and Al-Nassr (10 goals in 14 appearances).

Lionel Messi follows closely with over 820 goals, demonstrating his exceptional skill with FC Barcelona (672 goals in 778 appearances), Paris Saint-Germain (32 goals in 75 appearances), and Inter Miami (15 goals in 24 appearances).

Pele, a football legend, has netted more than 770 goals, notably at Santos (643 goals in 656 appearances) and New York Cosmos (36 goals in 64 appearances), among other clubs.

Josef Bican, known for his prolific scoring, accumulated over 760 goals, primarily with Slovan Bratislava (159 goals in 150 appearances) and Rapid Vienna (357 goals in 217 appearances).

Lastly, Romario, with over 750 goals, made significant contributions at clubs such as Vasco da Gama (71 goals in 106 appearances), Barcelona (39 goals in 65 appearances), and various Brazilian teams throughout his career.
"""


t = """Exploring the World of Cinematic Masterpieces: "Inception" and "Interstellar"
In the realm of modern cinema, few directors have crafted as many visually stunning and intellectually stimulating films as Christopher Nolan. His works, including the critically acclaimed Inception and Interstellar, continue to captivate audiences with their intricate narratives and groundbreaking concepts.

Inception (2010)

Released in 2010, Inception is a science fiction thriller that redefined the genre with its complex story and innovative visuals. Directed by Christopher Nolan, this film stars Leonardo DiCaprio and Joseph Gordon-Levitt, who deliver unforgettable performances. The plot centers around a skilled thief who is given a chance at redemption by planting an idea deep within a target’s subconscious. Produced by Warner Bros., the movie has a runtime of 148 minutes and remains a testament to Nolan’s visionary storytelling.

Interstellar (2014)

Building on the themes of exploration and survival, Nolan’s 2014 film Interstellar delves into the vastness of space with a new level of ambition. The film features Matthew McConaughey and Anne Hathaway in leading roles, navigating through a wormhole in a desperate bid to save humanity. Like Inception, Interstellar also bears the mark of Christopher Nolan’s direction and is produced by Paramount Pictures. The film runs for 169 minutes and continues to be praised for its scientific accuracy and emotional depth.

Connections and Themes

Both films share more than just their director. They explore profound themes through visually impressive and thought-provoking narratives. Nolan’s role as the director connects these cinematic pieces, showcasing his unique ability to blend complex plots with striking visuals. In Inception, Nolan’s portrayal of a layered dreamscape contrasts with the grand cosmic exploration in Interstellar, yet both films reflect his knack for pushing the boundaries of storytelling.

Behind the Scenes

Warner Bros., the production company behind Inception, is renowned for its role in delivering high-quality films to the audience. On the other hand, Paramount Pictures, which produced Interstellar, is equally celebrated for its contributions to the film industry. Both organizations played pivotal roles in bringing Nolan’s visionary concepts to life, demonstrating their influence in the cinematic world.

As we continue to explore Nolan’s filmography, Inception and Interstellar stand out not just for their box office success but for their ability to challenge and engage audiences with their ambitious storytelling. Whether through the exploration of dreams or space, Nolan’s films invite us to question reality and envision the impossible.
"""
# def fetch_wikipedia_page(title):
#     url = f"https://en.wikipedia.org/wiki/{title}"
#     response = requests.get(url)
#     soup = BeautifulSoup(response.text, 'html.parser')
#     return soup.get_text()

# source = [TEXT(fetch_wikipedia_page("List_of_men%27s_footballers_with_1,000_or_more_official_appearances"))]
db = FalkorDB(host='localhost', port=6379)
class FalkorDB_graph:
    def __init__(self, graph_name):
        self.graph = db.select_graph(graph_name)
        try:
            self.graph.delete()
        except:
            pass
    
    # Helper function to handle arrays
    def handle_array_attributes(self, attributes):
        handled_attributes = {}
        for key, value in attributes.items():
            # Convert the key to a string if it's an array (space-separated string)
            if isinstance(key, list):
                key = ' '.join(map(str, key))
            if isinstance(value, list):
                # Convert list to a space-separated string (or another preferred format)
                value = ' '.join(map(str, value))
            handled_attributes[key] = value
        return handled_attributes
    def create_node(self, node_id, node_type, attributes):
        handled_attributes = self.handle_array_attributes(attributes)

        cypher_query = f"CREATE (:{node_type.replace(' ', '')} {{id: '{node_id}', " + ', '.join([f"{k}: '{v}'" for k, v in handled_attributes.items()]) + "})"
        self.graph.query(cypher_query)
    
    def create_relationship(self, source_id, relation, target_id):
        cypher_query = f"""
        MATCH (a {{id: '{source_id}'}})
        MATCH (b {{id: '{target_id}'}})
        CREATE (a)-[:{relation.replace(' ', '_')}]->(b)
        """
        self.graph.query(cypher_query)
def kg_from_txt(file_path, boundaries):
    file_name = file_path.split(".")[0]
    source = [TEXT(src_files + file_path)]

    model = OpenAiGenerativeModel(model_name="gpt-4o")

    ontology = Ontology.from_sources(
        sources=source,
        boundaries=boundaries,
        model=model,
    )
    graph = db.select_graph(file_name + "_ontology")
    try:
        graph.delete()
    except:
        pass
    ontology.save_to_graph(graph)
    graph = db.select_graph(file_name)
    try:
        graph.delete()
    except:
        pass
    kg = KnowledgeGraph(
        name=file_name,
        model_config=KnowledgeGraphModelConfig.with_model(model),
        ontology=ontology,
    )
    kg.process_sources(source)
    
    return kg

def create_knowledge_graph_from_json(json_file_path):
    json_name = json_file_path.split(".")[0]
    kg = FalkorDB_graph(json_name + "_true")
    # Load JSON data
    with open(src_files + json_file_path, 'r') as file:
        data = json.load(file)
    
    # Create nodes in FalkorDB
    for node in data['nodes']:
        node_id = node['id']
        node_type = node['type']
        attributes = node['attributes']
        # print(node)
        kg.create_node(node_id, node_type, attributes)
    
    # Create relationships in FalkorDB
    for relationship in data['relationships']:
        source = relationship['source']
        relation = relationship['relation']
        target = relationship['target']
        kg.create_relationship(source, relation, target)
    
    print(f"{json_name} Knowledge Graph created successfully in FalkorDB!")



kgs = []
for file in os.listdir(src_files):
    if file.endswith(".txt"):
        boundaries = """"""
        #     Extract only footballers and their teams, appearances and goals.
        #     Do not create entities for what can be expressed as attributes.
        # """
        kgs.append(kg_from_txt(file, boundaries))
    elif file.endswith(".json"):
        create_knowledge_graph_from_json(file)




# print(kg.ask("how much teams Peter Shilton played"))
# print(kg.ask("what can you tell me about messi?"))

# ontology_ent = [en.label for en in ontology.entities]
# ontology_rel = [en.label for en in ontology.relations]

# graph_store = FalkorDBGraphStore(
#     "redis://localhost:6379", decode_responses=True
# )
# storage_context = StorageContext.from_defaults(graph_store=graph_store)
# relik = RelikPathExtractor(
#     model="relik-ie/relik-relation-extraction-small", model_config={"skip_metadata": True})
# Settings.llm = model
# Settings.chunk_size = 512
# documents = [
#     Document(text=t)
# ]
# index = PropertyGraphIndex.from_documents(
#     documents,
#     kg_extractors=[relik],
#     storage_context=storage_context,
#     show_progress=True
# )

# query_engine = index.as_query_engine(include_text=True)

# query_engine.query("how much teams Messi played?")
