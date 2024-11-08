import json
import os

import requests
from dotenv import load_dotenv

from AIService import AIService
from messenger import verify_task

PROMPT = "You are helpful assistant. Provide answer to the given questions."

load_dotenv()


def retrieve_data() -> str:
    api_key = os.environ.get("aidevs.api_key")
    api_key_pattern = os.environ.get("aidevs.s01e03.api_key_pattern")

    content = ""
    file_path = f"s01e03.txt"
    if not os.path.exists(file_path):
        # Fetch the content from the specified URL
        url = os.environ.get("aidevs.s01e03.file_url_prefix").replace(api_key_pattern, api_key)
        response = requests.get(url)
        content = response.text

        # Create the file and write the content to it
        with open(file_path, "w") as file:
            file.write(content)
    else:
        # Read the content of the file
        with open(file_path, "r") as file:
            content = file.read()
    return json.loads(content.replace(api_key_pattern, api_key))


def fix_data(data):
    aiservice = AIService()
    for item in data["test-data"]:
        recalculate_math_operation(item)
        answer_additional_question(aiservice, item)


def recalculate_math_operation(item):
    # Calculate the result of the question
    item["answer"] = str(eval(item["question"]))


def answer_additional_question(aiservice, item):
    # For those lines that have additional questions, get answers from llm
    if "test" in item:
        item["test"]["a"] = aiservice.answer(item["test"]["q"])


data = retrieve_data()
fix_data(data)
response_data = verify_task("JSON", data, os.environ.get("aidevs.s01e03.report_url"))
print(response_data)
