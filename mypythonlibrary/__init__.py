from __future__ import annotations
import streamlit as st
import pandas as pd
import numpy as np
import json
from aimodule import AIClient, ask_question
from article_metadata import add_article_image_urls
from dataloader import CSVLoader
from pydanticsheme import (
    NewsSummaryResponse,
    STRICT_NEWS_RESPONSE_FORMAT,
)
def format_news_for_terminal(result: NewsSummaryResponse) -> str:
    sections = []

    for item in result.news:
        sections.append(
            f"Company: {item.company_name}\n"
            f"Summary: {item.summary}\n"
            f"URL: {item.url}\n"
            f"Source: {item.source}\n"
            f"News ID: {item.id}\n"
            f"Expected price direction: {item.expected_price_direction}\n"
            f"Company impact: {item.company_impact}\n"
            f"Impact reasoning: {item.impact_reasoning}"
        )

    return "\n\n" + ("\n\n" + "-" * 60 + "\n\n").join(sections)

def ask_for_strict_news_summary(
    records: list[dict],
    model: str = "deepseek-ai/DeepSeek-V4-Flash",
) -> NewsSummaryResponse:
    client = AIClient()

    if client._client is None:
        raise RuntimeError("No API key/client is available.")

    response = client._client.chat.completions.create(
        model=model,
        response_format=STRICT_NEWS_RESPONSE_FORMAT,
        messages=[
            {
                "role": "system",
                "content": (
            "You are a careful financial-news analyst. Produce a useful, detailed "
            "summary for every supplied record. Each summary should be 3 to 5 "
            "sentences: explain what happened, who is affected, why it matters, "
            "and any likely business or market context that is supported by the "
            "record. Use the company name, headline, source, article URL, and image URL "
            "identify the story accurately. Do not invent facts, numbers, or "
            "article details that were not provided. If the article content is "
            "not available to you, say only what can reasonably be inferred from "
            "the supplied headline and metadata. For each item, assess the expected "
            "short-term price direction and company impact. Use uncertain or neutral "
            "when the evidence is insufficient; never present this assessment as financial advice. "
            "Return only JSON matching the response schema."
            "News ID, Source and URL are always provided so [None] is not a valid value. If the article URL is not provided, return [None] for the URL field."
             ),
                
            },
            {
                "role": "user",
                "content": (
                    f"News records to summarize:\n"
                    f"{json.dumps(records, ensure_ascii=False)}"
                ),
            },
        ],
    )

    return NewsSummaryResponse.model_validate_json(
        response.choices[0].message.content
    )
st.title("Cool News App")

def summarize_news(csv_path: str | None = None) -> str:
    loader = CSVLoader(csv_path)
    filters = loader.apply_keyword(loader.build_filters())

    if not filters:
        raise ValueError("Please provide at least one filter for the news search.")

    records = loader.get_fields(filters)

    if not records:
        return "No matching news found."

    if isinstance(records, list) and isinstance(records[0], dict):
        payload = records
    else:
        payload = [{"headline": item} for item in records]

    result = ask_for_strict_news_summary(add_article_image_urls(payload))
    return format_news_for_terminal(result)


def search_and_summarize(
    prompt: str,
    csv_path: str | None = None,
) -> str:
    loader = CSVLoader(csv_path)
    matching_records = loader.run_with_natural_language(prompt)

    if matching_records.empty:
        return "No matching news found for your query."

    result = ask_for_strict_news_summary(
        add_article_image_urls(matching_records.to_dict(orient="records"))
    )
    return format_news_for_terminal(result)


def main() -> None:
    query = input("What news would you like to search for? ").strip()
    if not query:
        print("Please enter a company, date, topic, or other news-search request.")
        return

    print(search_and_summarize(query))


if __name__ == "__main__":
    main()


__all__ = [
    "CSVLoader",
    "NewsSummaryResponse",
    "ask_question",
    "ask_for_strict_news_summary",
    "summarize_news",
    "search_and_summarize",
    "main",
]
