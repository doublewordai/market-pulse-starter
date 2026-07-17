from pydantic import BaseModel, ConfigDict
from typing import Literal, Optional

class NewsItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_name: str
    date: str
    summary: str
    url: Optional[str] = None
    source: Optional[str] = None
    id: Optional[str] = None
    expected_price_direction: Literal["increase", "decrease", "neutral", "uncertain"]
    company_impact: Literal["positive", "negative", "mixed", "neutral", "uncertain"]
    impact_reasoning: str


class NewsSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    news: list[NewsItem]


class NewsSearchFilters(BaseModel):

    model_config = ConfigDict(extra="forbid")

    company: str | None
    date: str | None
    from_date: str | None
    to_date: str | None
    headline: str | None
    id: str | None
    source: str | None
    url: str | None
    headline_keyword: str | None
    headline_keyword_exclude: str | None
    category: str | None


STRICT_NEWS_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "news_summary_response",
        "strict": True,
        "schema": NewsSummaryResponse.model_json_schema(),
    },
}

# The summary model is asked for ordinary JSON; Pydantic validates it strictly in Python.
# This is more broadly supported than provider-side JSON Schema enforcement.
SUMMARY_JSON_RESPONSE_FORMAT = {"type": "json_object"}


STRICT_SEARCH_FILTER_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "news_search_filters",
        "strict": True,
        "schema": NewsSearchFilters.model_json_schema(),
    },
}
