import os

import requests
from bs4 import BeautifulSoup
from deepdiff.serialization import json_loads
from dotenv import load_dotenv

from AIService import AIService
from AIStrategy import AIStrategy
from MP3ToTextStrategy import MP3ToTextStrategy
from PNGToTextStrategy import PNGToTextStrategy
from messenger import verify_task

ARTICLE_URL = os.environ.get("aidevs.s02e05.article_url")
PROMPT = """You are a helpful data analyst. Analyze the provided article to answer the questions given in the following format
01=What is the first question?
02=What is the second question? 
...
10=What is the tenth question?

The article is divided into sections. Audio and image files are included in the article as text. Based on the article, answer the questions and provide 
the answers in the following format skipping the new line characters:
{
"01": "Answer to the first question",
"02": "Answer to the second question",
"03": "Answer to the third question",
}

Pay special attention to the context of images and audio files.
Context: {context}
"""

folder = 'resources/s02e05'


class Context():

    def __init__(self) -> None:
        self._strategyDict = {}

    def register(self, strategy: AIStrategy) -> None:
        self._strategyDict[strategy.medium] = strategy

    def convert(self, file: str) -> str:
        ext = os.path.splitext(file)[1]
        strategy = self._strategyDict.get(ext)
        if strategy is None:
            return ""
        return strategy.convert(file)

    def build(self, url: str) -> str:
        context = PROMPT
        sections = []
        soup = BeautifulSoup(retrieve_text(url), 'html.parser')
        soup = self.strip_p_tags(soup)
        container = soup.find('div', class_='container')
        if not container:
            return []

        current_section = {'title': '', 'text': ''}
        for element in container.descendants:
            if element.name == 'h1':
                current_section['title'] = element.get_text(strip=True)
            elif element.name == 'h2':
                if current_section['text']:
                    sections.append(current_section)
                current_section = {'title': element.get_text(strip=True), 'text': ''}
            elif element.name == 'figure':
                img_tag = element.find('img')
                figcaption_tag = element.find('figcaption')
                if img_tag and figcaption_tag:
                    img_url = f"https://centrala.ag3nts.org/dane/{img_tag['src']}"
                    img_file_path = retrieve_and_save_file(folder, img_url)
                    current_section[
                        'text'] += f"Image (caption: {figcaption_tag.get_text(strip=True)}): {self.convert(img_file_path)} "
            elif element.name == 'audio' and 'controls' in element.attrs:
                source_tag = element.find('source')
                if source_tag and 'src' in source_tag.attrs:
                    audio_url = f"https://centrala.ag3nts.org/dane/{source_tag['src']}"
                    audio_file_path = retrieve_and_save_file(folder, audio_url)
                    current_section['text'] += f"Audio transcription: {self.convert(audio_file_path)} "
            elif element.string:
                current_section['text'] += element.string.strip() + ' '
        if current_section['text']:
            sections.append(current_section)

        for section in sections:
            context += f"Section: {section['title']}\n"
            context += " ".join(section['text']) + "\n"
        return context

    def strip_p_tags(self, soup):
        for p in soup.find_all('p'):
            p.unwrap()  # Remove the <p> tag but keep its content
        return soup


def retrieve_and_save_file(folder, url) -> str:
    response = requests.get(url)
    response.raise_for_status()  # Ensure the request was successful
    file_path = f"{folder}/{os.path.basename(url)}"
    with open(file_path, "wb") as file:
        file.write(response.content)
    return file_path


def retrieve_text(article_url) -> []:
    # Fetch the content from the specified URL

    response = requests.get(article_url)
    response.raise_for_status()  # Ensure the request was successful
    return response.text


# Function to extract text, images, and audio links
def extract_content(soup):
    text_content = soup.get_text()
    images = [img['src'] for img in soup.find_all('img')]
    audio_links = [audio['src'] for audio in soup.find_all('audio')]
    return text_content, images, audio_links


def build_context(sections):
    context = PROMPT
    for section in sections:
        context += f"Section: {section['title']}\n"
        context += " ".join(section['text']) + "\n"
    return context


load_dotenv()
questions = retrieve_text(os.environ.get("aidevs.s02e05.questions_url"))

# article = strip_p_tags(soup)
context = Context()
context.register(MP3ToTextStrategy())
context.register(PNGToTextStrategy())

contextString = context.build(os.environ.get("aidevs.s02e05.article_url"))
# context = build_context(sections)
answers = AIService().answer(questions, contextString)

print(questions)
print(answers)

response_data = verify_task(
    "arxiv", json_loads(answers), os.environ.get("aidevs.report_url"))
print(response_data)