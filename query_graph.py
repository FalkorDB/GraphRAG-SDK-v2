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
from fixtures.prompts import (
    GRAPH_QA_SYSTEM,
    GRAPH_QA_PROMPT,
    CYPHER_GEN_SYSTEM,
    CYPHER_GEN_PROMPT,
    CYPHER_GEN_PROMPT_WITH_ERROR,
)
import time

load_dotenv()

CONFIG = {
    "ontology_file": "ontology.json",
    "cypher": {
        "model_name": "gemini-1.5-pro-preview-0409",
        "max_output_tokens": 8192,
        "max_input_characters": 500000,
        "temperature": 0,
        "top_p": 0.95,
        "ontology_file": "ontology.json",
    },
    "qa": {
        "model_name": "gemini-1.5-pro-preview-0409",
        "max_output_tokens": 8192,
        "max_input_characters": 500000,
        "temperature": 0,
        "top_p": 0.95,
    },
}


def _load_config():
    global CONFIG
    with open("config.yaml", "r") as f:
        values = yaml.safe_load(f)["query_graph"]
        CONFIG.update(values)

    print(f"Loaded config: {CONFIG}")


def extract_cypher(text: str):

    if not text.startswith("```"):
        return text

    regex = r"```(?:cypher)?(.*?)```"
    matches = re.findall(regex, text, re.DOTALL)

    return "".join(matches)


def verify_cypher_labels(cypher: str, ontology: Ontology):
    try:
        if not cypher or len(cypher) == 0:
            return "Cypher statement is empty"

        not_found_node_labels = []
        node_labels = re.findall(r"\(:(.*?)\)", cypher)
        for label in node_labels:
            label = label.split(":")[1] if ":" in label else label
            label = label.split("{")[0].strip() if "{" in label else label
            if label not in [node.label for node in ontology.nodes]:
                not_found_node_labels.append(label)

        not_found_edge_labels = []
        edge_labels = re.findall(r"\[:(.*?)\]", cypher)
        for label in edge_labels:
            label = label.split(":")[1] if ":" in label else label
            label = label.split("{")[0].strip() if "{" in label else label
            if label not in [edge.label for edge in ontology.edges]:
                not_found_edge_labels.append(label)

        if len(not_found_node_labels) > 0 or len(not_found_edge_labels) > 0:
            return f"""
    The following labels were not found in the ontology:
    Nodes: {set(not_found_node_labels)}
    Edges: {set(not_found_edge_labels)}
    """
        return True
    except Exception as e:
        print(f"Failed to verify cypher labels: {e}")
        return e


def get_next_question(
    g: Graph,
    ontology: Ontology,
    cypher_chat: ChatSession,
    qa_session: ChatSession,
    retries=5,
):

    question = input("Enter a question:\n")

    # print(f"Cypher statement: {cypher_statement_response}")

    error = False
    cypher = ""
    timer = time.time()
    while error is not None and retries > 0:
        try:
            cypher_prompt = (
                CYPHER_GEN_PROMPT.format(question=question)
                if error is False
                else CYPHER_GEN_PROMPT_WITH_ERROR.format(question=question, error=error)
            )
            cypher_statement_response = cypher_chat.send_message(
                cypher_prompt,
            )
            cypher = extract_cypher(cypher_statement_response.text)
            print(f"Cypher: {cypher}")
            is_valid = verify_cypher_labels(cypher, ontology)
            # print(f"Is valid: {is_valid}")
            if is_valid is not True:
                raise Exception(is_valid)
            results = g.query(cypher).result_set
            if len(results) == 0:
                raise Exception("No results found")
            error = None
        except Exception as e:
            # print(f"Error: {e}")
            error = e
            retries -= 1

    if not isinstance(results, list) or len(results) == 0:
        context = str(results).strip()
    elif not isinstance(results[0], list):
        context = str(results).strip()
    else:
        for (l, _) in enumerate(results):
            if not isinstance(results[l], list):
                results[l] = str(results[l])
            else:
                for (i, __) in enumerate(results[l]):
                    results[l][i] = str(results[l][i])
        context = str(results).strip()


    qa_prompt = GRAPH_QA_PROMPT.format(
        context=context, cypher=cypher, question=question
    )
    # print(f"QA prompt: {qa_prompt}")
    qa_response = qa_session.send_message(qa_prompt)

    print(f"QA response: {qa_response.text}")
    print(f"Time taken: {round(time.time() - timer, 2)}")


def main():

    try:

        # Create an ArgumentParser object
        parser = argparse.ArgumentParser(description="Knowledge graph QA")

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

        # Parse the command-line arguments
        args = parser.parse_args()

        # Access the parsed arguments
        if args.project:
            os.environ["PROJECT_ID"] = args.project
        if args.region:
            os.environ["REGION"] = args.region
        falkordb_config = {
            "host": args.host,
            "port": args.port,
            "username": args.username,
            "password": args.password,
        }
        graph_id = args.graph_id

        vertexai.init(project=os.getenv("PROJECT_ID"), location=os.getenv("REGION"))

        db = FalkorDB(**falkordb_config)
        g = db.select_graph(graph_id)

        ontology = None
        with open(CONFIG["ontology_file"], "r", encoding="utf-8") as f:
            ontology = Ontology.from_json(f.read())

        cypher_assistant = GenerativeModel(
            model_name=CONFIG["cypher"]["model_name"],
            generation_config={
                "max_output_tokens": CONFIG["cypher"]["max_output_tokens"],
                "temperature": CONFIG["cypher"]["temperature"],
                "top_p": CONFIG["cypher"]["top_p"],
            },
            system_instruction=CYPHER_GEN_SYSTEM.format(ontology=ontology.to_json()),
        )

        qa_assistant = GenerativeModel(
            model_name=CONFIG["qa"]["model_name"],
            generation_config={
                "max_output_tokens": CONFIG["qa"]["max_output_tokens"],
                "temperature": CONFIG["qa"]["temperature"],
                "top_p": CONFIG["qa"]["top_p"],
            },
            system_instruction=GRAPH_QA_SYSTEM,
        )

        cypher_chat = cypher_assistant.start_chat()
        qa_chat = qa_assistant.start_chat()

        while True:
            get_next_question(
                g,
                ontology,
                cypher_chat,
                qa_chat,
            )

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    _load_config()
    main()
