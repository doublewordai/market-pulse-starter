import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI
from typing import Optional
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
SUMMARY_MODEL = os.getenv("MODEL_NAME", "Qwen/Qwen3.6-35B-A3B-FP8")

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
        model: str = SUMMARY_MODEL,
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
    
    # Inject current year into instructions
    current_year = datetime.now().year
    instructions_str = json.dumps(instructions, ensure_ascii=False)
    instructions_str = instructions_str.replace("current year", f"current year ({current_year})")

    response = client._client.chat.completions.create(
        model=model,
        response_format=STRICT_SEARCH_FILTER_RESPONSE_FORMAT,
        messages=[
            {
                "role": "system",
                "content": (
                    "Follow these conversion instructions exactly. Return only JSON that "
                    "matches the response schema.\n\n"
                    f"{instructions_str}"
                ),
            },
            {"role": "user", "content": query},
        ],
    )

    filters = NewsSearchFilters.model_validate_json(
        response.choices[0].message.content
    )
    return filters.model_dump(exclude_none=True)


def load_company_symbols() -> dict:
    """Load company name to stock symbol mappings from JSON file."""
    try:
        symbols_path = Path(__file__).with_name("company_symbols.json")
        with symbols_path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        # Return empty dict if file not found
        return {}

def convert_company_to_symbol(company_name: str, symbol_mapping: dict) -> str:
    """Convert company name to stock symbol using mapping."""
    company_lower = company_name.lower().strip()
    return symbol_mapping.get(company_lower, company_name.upper())

def convert_symbols_to_company_names_in_data(data: list[dict]) -> list[dict]:
    """Convert stock symbols to company names in data using AI."""
    # Use simple mapping directly (more reliable than AI for this task)
    symbol_mapping = load_company_symbols()
    
    # Use reverse_mapping if available, otherwise build it
    if "reverse_mapping" in symbol_mapping:
        reverse_mapping = symbol_mapping["reverse_mapping"]
    else:
        reverse_mapping = {v.upper(): k.title() for k, v in symbol_mapping.items() if not isinstance(v, dict)}
    
    for record in data:
        if "company" in record:
            company_upper = record["company"].upper().strip()
            if company_upper in reverse_mapping:
                record["company"] = reverse_mapping[company_upper]
    return data

def extract_finnhub_parameters(
    query: str,
    model: str = FILTERING_MODEL,
) -> dict:
    """Extract Finnhub API parameters from natural language query.
    
    Returns dict with keys:
    - symbols: list of stock symbols (e.g., ["AAPL", "MSFT"])
    - category: news category (e.g., "general", "forex", "crypto") or None
    - from_date: start date in YYYY-MM-DD format
    - to_date: end date in YYYY-MM-DD format
    """
    filtering_api_key = os.getenv("DOUBLEWORD_API_KEY2")
    if not filtering_api_key:
        raise RuntimeError("DOUBLEWORD_API_KEY2 is not configured for parameter extraction.")

    client = AIClient(api_key=filtering_api_key)
    if client._client is None:
        raise RuntimeError("No API key/client is available.")

    # Load company symbol mapping
    symbol_mapping = load_company_symbols()
    
    # Create mapping string for the AI
    mapping_examples = ", ".join([f'"{k}": "{v}"' for k, v in list(symbol_mapping.items())[:10]])
    
    system_prompt = """You are a financial data extraction assistant. Extract parameters for the Finnhub API from natural language queries.

Extract the following information from the user's query:
1. Stock symbols (e.g., AAPL, MSFT, GOOGL) - return as a list
2. News category (general, forex, crypto, merger, technical) - return as string or null
3. Date range - extract from_date and to_date in YYYY-MM-DD format

Rules:
- Convert company names to stock symbols using this mapping: {mapping_examples}
- If a company name is mentioned but not in the mapping, convert it to uppercase (e.g., "Apple" -> "APPLE")
- If no specific symbols are mentioned, return an empty list
- If no category is mentioned, return null
- If no date range is mentioned, use the last 7 days from today
- Current date: {current_date}
- Return valid JSON only, no explanations

Example output format:
{{
    "symbols": ["AAPL", "MSFT"],
    "category": "general",
    "from_date": "2026-07-01",
    "to_date": "2026-07-31"
}}"""

    current_date = datetime.now().strftime("%Y-%m-%d")
    system_prompt = system_prompt.format(
        current_date=current_date,
        mapping_examples=mapping_examples
    )

    response = client._client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {"role": "user", "content": query},
        ],
    )

    try:
        params = json.loads(response.choices[0].message.content)
        
        # Post-process symbols to ensure they're in the correct format
        if "symbols" in params and params["symbols"]:
            processed_symbols = []
            for symbol in params["symbols"]:
                symbol_upper = symbol.upper().strip()
                # Check if it's a company name that needs conversion
                if symbol_upper in symbol_mapping:
                    processed_symbols.append(symbol_mapping[symbol_upper])
                elif symbol_upper.lower() in symbol_mapping:
                    processed_symbols.append(symbol_mapping[symbol_upper.lower()])
                else:
                    # Assume it's already a symbol or convert to uppercase
                    processed_symbols.append(symbol_upper)
            params["symbols"] = processed_symbols
        
        return params
    except json.JSONDecodeError:
        # Fallback to default parameters
        return {
            "symbols": [],
            "category": None,
            "from_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
            "to_date": datetime.now().strftime("%Y-%m-%d")
        }

