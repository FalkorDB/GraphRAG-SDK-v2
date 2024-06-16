from dotenv import load_dotenv
import re
import requests
import os
from falkordb import FalkorDB, Graph
from bs4 import BeautifulSoup
import json
import vertexai
from vertexai.generative_models import (
    GenerativeModel,
    HarmCategory,
    HarmBlockThreshold,
    ChatSession,
)
from classes.onotology import Ontology
import argparse
import yaml
from fixtures.prompts import EXTRACT_DATA_SYSTEM, EXTRACT_DATA_PROMPT
from classes.scrape_cache import ScrapeCache
from concurrent.futures import Future, ThreadPoolExecutor, wait

load_dotenv()

cache: ScrapeCache = None

CONFIG = {
    "model_name": "gemini-1.5-pro-preview-0409",
    "max_output_tokens": 8192,
    "max_input_characters": 500000,
    "temperature": 0,
    "top_p": 0.95,
    "ontology_file": "ontology.json",
    "cache_file": "scrape_cache.json",
    "max_workers": 16,
}


def _load_config():
    global CONFIG
    with open("config.yaml", "r") as f:
        values = yaml.safe_load(f)["extract_data"]
        CONFIG.update(values)

    print(f"Loaded config: {CONFIG}")


def map_dict_to_cypher_properties(d: dict):
    cypher = "{"
    for key, value in d.items():
        # Check value type
        if isinstance(value, str):
            # Find unescaped quotes
            reg = r"((?<!\\)(\"))|((?<!\\)(\'))"
            search = re.search(reg, value)
            if search:
                i = 0
                for match in re.finditer(reg, value):
                    value = (
                        value[: match.start() + i] + "\\" + value[match.start() + i :]
                    )
                    i += 1
            value = f'"{value}"' if f"{value}" != "None" else '""'
        else:
            value = str(value) if f"{value}" != "None" else '""'
        cypher += f"{key}: {value}, "
    cypher = (cypher[:-2] if len(cypher) > 1 else cypher) + "}"
    return cypher


def fix_missing_str_escape_in_json(json_str: str):
    return re.sub(r'\\(?=")', r"\\\\", json_str)


def create_node(graph: Graph, args: dict, ontology: Ontology):
    # Get unique attributes from node
    node = ontology.get_node_with_label(args["label"])
    if node is None:
        print(f"Node with label {args['label']} not found in ontology")
        return None
    unique_attributes_schema = [attr for attr in node.attributes if attr.unique]
    unique_attributes = {
        attr.name: args["attributes"][attr.name] for attr in unique_attributes_schema
    }
    unique_attributes_text = map_dict_to_cypher_properties(unique_attributes)
    non_unique_attributes = {
        attr.name: args["attributes"][attr.name]
        for attr in node.attributes
        if not attr.unique and attr.name in args["attributes"]
    }
    non_unique_attributes_text = map_dict_to_cypher_properties(non_unique_attributes)
    set_statement = (
        f"SET n += {non_unique_attributes_text}"
        if len(non_unique_attributes.keys()) > 0
        else ""
    )
    query = f"MERGE (n:{args['label']} {unique_attributes_text}) {set_statement}"
    print(f"Query: {query}")
    result = graph.query(query)
    return result


def create_edge(graph: Graph, args: dict, ontology: Ontology):
    edge = ontology.get_edge_with_label(args["label"])
    if edge is None:
        print(f"Edge with label {args['label']} not found in ontology")
        return None
    source_unique_attributes = args["source"]["attributes"]
    source_unique_attributes_text = map_dict_to_cypher_properties(
        source_unique_attributes
    )

    target_unique_attributes = args["target"]["attributes"]
    target_unique_attributes_text = map_dict_to_cypher_properties(
        target_unique_attributes
    )

    edge_attributes = (
        map_dict_to_cypher_properties(args["attributes"])
        if "attributes" in args
        else {}
    )
    set_statement = (
        f"SET r += {edge_attributes}"
        if "attributes" in args and len(args["attributes"].keys()) > 0
        else ""
    )
    query = f"MATCH (s:{args['source']['label']} {source_unique_attributes_text}) MATCH (d:{args['target']['label']} {target_unique_attributes_text}) MERGE (s)-[r:{args['label']}]->(d) {set_statement}"
    print(f"Query: {query}")
    result = graph.query(query)
    return result


def extract_json(text: str):

    if not text.startswith("```"):
        return text

    regex = r"```(?:json)?(.*?)```"
    matches = re.findall(regex, text, re.DOTALL)

    return "".join(matches)


def process_url(chat_session: ChatSession, graph: Graph, url: str, ontology: Ontology):
    print(f"Processing URL: {url}")

    text = cache.get(url)
    if text is None:
        html_content = requests.get(url, timeout=5).text
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text()
        text = re.sub(r"\n{2,}", "\n", text)
        cache.set(url, text)
    else:
        print("Using cached text")

    text = text[: CONFIG["max_input_characters"]]
    user_message = EXTRACT_DATA_PROMPT.format(
        text=f"""
URL: {url}
Text: {text}
"""
    )

    model_response = chat_session.send_message(user_message)
    print(f"User message: {user_message}")
    print(f"Model response: {model_response.text}")

    data = json.loads(extract_json(model_response.text))

    for node in data["nodes"]:
        try:
            create_node(graph, node, ontology)
        except Exception as e:
            print(f"Exception while creating node: {e}")
            continue

    for edge in data["edges"]:
        try:
            create_edge(graph, edge, ontology)
        except Exception as e:
            print(f"Exception while creating edge: {e}")
            continue


def main():
    global cache
    try:

        # Create an ArgumentParser object
        parser = argparse.ArgumentParser(description="Knowledge graph builder")

        # Add arguments
        parser.add_argument(
            "--project",
            help="Vertex AI project ID",
        )
        parser.add_argument(
            "--region",
            help="Vertex AI region",
        )
        parser.add_argument("--host", help="FalkorDB host", default="localhost")
        parser.add_argument("--port", help="FalkorDB port", default=6379)
        parser.add_argument("--username", help="FalkorDB user", default=None)
        parser.add_argument("--password", help="FalkorDB password", default=None)
        parser.add_argument(
            "graph_id", help="ID of the graph to store the extracted data"
        )
        parser.add_argument(
            "sources", help="File containing list of URLs to extract knowledge from"
        )

        # Parse the command-line arguments
        args = parser.parse_args()

        # Access the parsed arguments
        if args.project:
            os.environ["PROJECT_ID"] = args.project
        if args.region:
            os.environ["REGION"] = args.region
        src_file = args.sources
        falkordb_config = {
            "host": args.host,
            "port": args.port,
            "username": args.username,
            "password": args.password,
        }
        graph_id = args.graph_id

        source_urls = []
        with open(src_file, "r", encoding="utf-8") as file:
            source_urls = file.readlines()

        vertexai.init(project=os.getenv("PROJECT_ID"), location=os.getenv("REGION"))
        generation_config = {
            "max_output_tokens": CONFIG["max_output_tokens"],
            "temperature": CONFIG["temperature"],
            "top_p": CONFIG["top_p"],
        }

        db = FalkorDB(**falkordb_config)

        cache = ScrapeCache(CONFIG["cache_file"]).load()

        g = db.select_graph(graph_id)

        ontology = None
        with open(CONFIG["ontology_file"], "r", encoding="utf-8") as f:
            ontology = Ontology.from_json(f.read())

        if ontology is None or ontology.validate_nodes() is False:
            raise Exception("Invalid ontology")

        assistant = GenerativeModel(
            CONFIG["model_name"],
            system_instruction=EXTRACT_DATA_SYSTEM + json.dumps(ontology.to_json()),
            generation_config=generation_config,
            # safety_settings={
            #     HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            #     HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            #     HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            #     HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            #     HarmCategory.HARM_CATEGORY_UNSPECIFIED: HarmBlockThreshold.BLOCK_NONE,
            # },
        )

        chat_session = assistant.start_chat()

        tasks = []
        with ThreadPoolExecutor(max_workers=CONFIG["max_workers"]) as executor:
            # extract entities and relationships from each page
            for url in source_urls:
                task = executor.submit(process_url, chat_session, g, url, ontology)
                tasks.append(task)

            # Wait for all tasks to complete
            wait(tasks)

    except Exception as e:
        if cache is not None:
            try:
                cache.save()
            except Exception as f:
                print(f"Error saving cache: {f}")
        raise e


if __name__ == "__main__":
    _load_config()
    main()
