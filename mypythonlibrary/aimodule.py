import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

try:
    from .pydanticsheme import (
        NewsSearchFilters,
        STRICT_SEARCH_FILTER_RESPONSE_FORMAT,
    )
except ImportError:
    from pydanticsheme import (
        NewsSearchFilters,
        STRICT_SEARCH_FILTER_RESPONSE_FORMAT,
    )

load_dotenv()

FILTERING_MODEL = "Qwen/Qwen3-VL-235B-A22B-Instruct-FP8"

class AIClient:

    def __init__(self, api_key: str | None = None, base_url: str = "https://api.doubleword.ai/v1"):
        if api_key is None:
            api_key = (
                os.getenv("DOUBLEWORD_API_KEY")
                or os.getenv("OPENAI_API_KEY")
                or os.getenv("API_KEY")
            )
        try:
            if api_key:
                self._client = OpenAI(api_key=api_key, base_url=base_url)
            else:
                self._client = None
        except Exception:
            # If the OpenAI client fails to initialize (missing creds or other), keep None
            self._client = None
def ask(
    self,
    prompt: str,
    model: str = "deepseek-ai/DeepSeek-V4-Flash",
    system: str | None = None,
    response_format: dict | None = None,
):
    messages = []

    if system:
        messages.append({"role": "system", "content": system})

    messages.append({"role": "user", "content": prompt})

    request = {
        "model": model,
        "messages": messages,
    }

    if response_format is not None:
        request["response_format"] = response_format

    resp = self._client.chat.completions.create(**request)
    return resp.choices[0].message.content
def ask_question(prompt: str | None = None, **kwargs):
    if prompt is None:
        prompt = input("Enter your message to the AI: ").strip()

    if not prompt:
        raise ValueError("It's not nice to ask the AI nothing. Please provide a prompt.")

    kwargs.setdefault(
        "system",
        "You are a helpful assistant. Respond in English only, clearly and concisely.",
    )

    client = AIClient()
    return client.ask(prompt, **kwargs)


def extract_news_search_filters(
    query: str,
    model: str = FILTERING_MODEL,
) -> dict[str, str]:
    """Turn a free-text request into filters accepted by CSVLoader.find_records."""
    filtering_api_key = os.getenv("DOUBLEWORD_API_KEY2")
    if not filtering_api_key:
        raise RuntimeError("DOUBLEWORD_API_KEY2 is not configured for filter extraction.")

    client = AIClient(api_key=filtering_api_key)
    if client._client is None:
        raise RuntimeError("No API key/client is available.")

    instructions_path = Path(__file__).with_name("search_conversion_instructions.json")
    with instructions_path.open("r", encoding="utf-8") as file:
        instructions = json.load(file)

    response = client._client.chat.completions.create(
        model=model,
        response_format=STRICT_SEARCH_FILTER_RESPONSE_FORMAT,
        messages=[
            {
                "role": "system",
                "content": (
                    "Follow these conversion instructions exactly. Return only JSON that "
                    "matches the response schema.\n\n"
                    f"{json.dumps(instructions, ensure_ascii=False)}"
                ),
            },
            {"role": "user", "content": query},
        ],
    )

    filters = NewsSearchFilters.model_validate_json(
        response.choices[0].message.content
    )
    return filters.model_dump(exclude_none=True)

