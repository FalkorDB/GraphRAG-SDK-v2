from dotenv import load_dotenv
import re
import requests
import os
from bs4 import BeautifulSoup
import json
import vertexai
from vertexai.generative_models import (
    GenerativeModel,
    HarmCategory,
    HarmBlockThreshold,
    ChatSession,
)
from falkordb import FalkorDB, Graph
import yaml
from random import shuffle
from math import ceil
import argparse
from fixtures.prompts import (
    CREATE_ONTOLOGY_SYSTEM,
    CREATE_ONTOLOGY_PROMPT,
    UPDATE_ONTOLOGY_PROMPT,
    FIX_ONTOLOGY_PROMPT,
)
from classes.onotology import Ontology
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
    "min_urls_count": 10,
    "output_file": "ontology.json",
    "cache_file": "scrape_cache.json",
    "max_workers": 16,
}


def _load_config():
    global CONFIG
    with open("config.yaml", "r") as f:
        values = yaml.safe_load(f)["ontology"]
        CONFIG.update(values)

    print(f"Loaded config: {CONFIG}")


def extract_json(text: str):
    regex = r"```(?:json)?(.*?)```"
    matches = re.findall(regex, text, re.DOTALL)

    return "".join(matches)


def process_url(chat_session: ChatSession, url: str, o: Ontology):
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
    user_message = (
        CREATE_ONTOLOGY_PROMPT.format(text=text)
        # if o == ""
        # else UPDATE_ONTOLOGY_PROMPT.format(text=text, ontology=o)
    )

    model_response = chat_session.send_message(user_message)

    # print(f"User message: {user_message}")
    print(f"Model response: {model_response}")

    if (
        model_response.usage_metadata.candidates_token_count
        >= CONFIG["max_output_tokens"]
    ):
        # TODO: Handle this case
        raise Exception("Model response exceeds token limit")

    try:
        new_ontology = Ontology.from_json(extract_json(model_response.text))
    except Exception as e:
        print(f"Exception while extracting JSON: {e}")
        new_ontology = None

    if new_ontology is not None:
        o = o.merge_with(new_ontology)

    return o


def fix_ontology(chat_session: ChatSession, o: Ontology):
    print(f"Fixing ontology...")

    user_message = FIX_ONTOLOGY_PROMPT.format(ontology=o)

    model_response = chat_session.send_message(user_message)

    # print(f"User message: {user_message}")
    print(f"Model response: {model_response}")

    if (
        model_response.usage_metadata.candidates_token_count
        >= CONFIG["max_output_tokens"]
    ):
        # TODO: Handle this case
        raise Exception("Model response exceeds token limit")

    try:
        new_ontology = Ontology.from_json(extract_json(model_response.text))
    except Exception as e:
        print(f"Exception while extracting JSON: {e}")
        new_ontology = None

    if new_ontology is not None:
        o = o.merge_with(new_ontology)

    return o


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
        parser.add_argument("--graph_id", help="ID of the graph to store the ontology")
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

        db = FalkorDB(**falkordb_config)

        cache = ScrapeCache(CONFIG["cache_file"]).load()

        source_urls = []
        with open(src_file, "r", encoding="utf-8") as file:
            source_urls = file.readlines()

        shuffle(source_urls)

        vertexai.init(project=os.getenv("PROJECT_ID"), location=os.getenv("REGION"))
        generation_config = {
            "max_output_tokens": CONFIG["max_output_tokens"],
            "temperature": CONFIG["temperature"],
            "top_p": CONFIG["top_p"],
        }

        boundaries = input(
            "Enter your boundaries instructions for the ontology extraction:\n"
        )

        assistant = GenerativeModel(
            CONFIG["model_name"],
            system_instruction=CREATE_ONTOLOGY_SYSTEM.replace(
                "#BOUNDARIES", boundaries
            ),
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

        ontology = Ontology()

        urls_for_ontology_count = max(
            min(10, ceil(len(source_urls) * 0.1)), CONFIG["min_urls_count"]
        )
        urls_for_ontology = source_urls[:urls_for_ontology_count]

        print(
            f"Using {urls_for_ontology_count} of {len(source_urls)} URLs for ontology extraction"
        )

        tasks: list[Future[Ontology]] = []
        with ThreadPoolExecutor(max_workers=CONFIG["max_workers"]) as executor:
            # extract entities and relationships from each page
            for url in urls_for_ontology:
                task = executor.submit(process_url, chat_session, url, ontology)
                tasks.append(task)

            # Wait for all tasks to complete
            wait(tasks)

        for task in tasks:
            ontology = ontology.merge_with(task.result())

        ontology = fix_ontology(chat_session, ontology)

        ontology = json.loads(ontology) if isinstance(ontology, str) else ontology

        ontology.discard_nodes_without_edges()
        ontology.discard_edges_without_nodes()

        ontology.validate_nodes()

        print("Final ontology:\n{ontology}".format(ontology=ontology))

        with open(CONFIG["output_file"], "w", encoding="utf-8") as f:
            f.write(json.dumps(ontology.to_json(), indent=2))
            f.close()

        if graph_id is not None:
            print(f"Saving ontology to graph {graph_id}")
            ontology.save_to_graph(
                db.select_graph(
                    graph_id if graph_id.endswith("schema") else f"{graph_id}_schema"
                )
            )
    except Exception as e:
        if cache is not None:
            cache.save()
        raise e


if __name__ == "__main__":
    _load_config()
    main()
