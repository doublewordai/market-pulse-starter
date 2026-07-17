import pandas as pd
import json
import sys
import os
from pathlib import Path

# Add parent directory to path for absolute imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from mypythonlibrary.aimodule import AIClient, SUMMARY_MODEL, extract_finnhub_parameters, convert_symbols_to_company_names_in_data
from mypythonlibrary.article_metadata import add_article_context
from mypythonlibrary.dataloader import CSVLoader, FinnhubLoader
from mypythonlibrary.pydanticsheme import (
    NewsSummaryResponse,
    STRICT_NEWS_RESPONSE_FORMAT,
)

NEWS_SUMMARY_SYSTEM_PROMPT = (
    "You are a careful financial-news analyst. Produce a detailed, informative "
    "summary for every supplied record. Each summary should be 6 to 10 sentences: "
    "explain what happened, who is affected, why it matters, and any likely business "
    "or market context supported by the record. When article_text is provided for a "
    "record, read and use that full article body as your primary source. Weave in "
    "specific facts, quotes, numbers, and developments from article_text rather than "
    "relying only on the headline. When article_fetched is true, the article was "
    "successfully downloaded from the URL and must inform the summary. When "
    "article_fetched is false or article_text is missing, say only what can be "
    "reasonably inferred from the headline and metadata. Use the company name, date, "
    "headline, source, article URL, and image URL to identify the story accurately. "
    "Do not invent facts, numbers, or article details that were not provided. "
    "Always include the publication date in the date field, using the record's date "
    "value when present and otherwise inferring the best available date from the "
    "article text. For each item, assess the expected short-term price direction and "
    "company impact. Use uncertain or neutral when the evidence is insufficient; "
    "never present this assessment as financial advice. Return only JSON matching "
    "the response schema. Write in clear English. Make each summary substantial and "
    "informative, not just a rewording of the headline. News ID, Source, URL, and "
    "date are always provided, so [None] is not a valid value for those fields. "
    "If the article URL is not provided, return [None] for the URL field. It is "
    "better to say that impact/direction is positive/negative/neutral than "
    "uncertain. If the article is not relevant to the company, say that the impact "
    "is neutral and the expected price direction is uncertain. "
    "IMPORTANT: Always use normal company names (e.g., 'Apple', 'Microsoft', 'Tesla') "
    "instead of stock symbols (e.g., 'AAPL', 'MSFT', 'TSLA'). Convert any stock symbols "
    "in the company_name field to their corresponding company names. Common conversions: "
    "AAPL -> Apple, MSFT -> Microsoft, GOOGL -> Google/Alphabet, AMZN -> Amazon, "
    "TSLA -> Tesla, NVDA -> NVIDIA, META -> Meta/Facebook, NFLX -> Netflix, DIS -> Disney, "
    "INTC -> Intel, AMD -> AMD, CSCO -> Cisco, ADBE -> Adobe, CRM -> Salesforce, ORCL -> Oracle, "
    "IBM -> IBM, AVGO -> Broadcom, JPM -> JPMorgan, V -> Visa, PG -> Procter & Gamble, "
    "JNJ -> Johnson & Johnson, BRK.B -> Berkshire Hathaway. Use the full company name in "
    "your summary, not the stock symbol."
)

def ask_for_strict_news_summary(
    records: list[dict],
    model: str = SUMMARY_MODEL,
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
                "content": NEWS_SUMMARY_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    f"News records to summarise:\n"
                    f"{json.dumps(records, ensure_ascii=False)}"
                ),
            },
        ],
    )

    return NewsSummaryResponse.model_validate_json(
        response.choices[0].message.content
    )


def search_headlines(
    prompt: str,
    csv_path: str | None = None,
    symbols: list[str] | None = None,
    category: str | None = None,
) -> tuple[pd.DataFrame, int]:
    """Search headlines without summarization.
    
    Args:
        prompt: Search query for natural language processing
        csv_path: Path to CSV file (if using CSV source)
        symbols: List of stock symbols (if using Finnhub API directly)
        category: News category for general market news (if using Finnhub API directly)
    
    Returns:
        tuple: (matching records DataFrame, total number of matching records)
    """
    if symbols or category:
        # Use Finnhub API with direct parameters (from UI)
        loader = FinnhubLoader(symbols, prompt, category)
        matching_records = loader.run_with_natural_language(prompt)
        
        # Convert stock symbols to company names in the data
        if not matching_records.empty:
            data_list = matching_records.to_dict('records')
            converted_data = convert_symbols_to_company_names_in_data(data_list)
            matching_records = pd.DataFrame(converted_data)
    elif csv_path:
        # Use CSV file
        loader = CSVLoader(csv_path)
        matching_records = loader.run_with_natural_language(prompt)
        
        # Convert stock symbols to company names in the data
        if not matching_records.empty:
            data_list = matching_records.to_dict('records')
            converted_data = convert_symbols_to_company_names_in_data(data_list)
            matching_records = pd.DataFrame(converted_data)
    else:
        # Use AI to extract Finnhub parameters from natural language
        try:
            params = extract_finnhub_parameters(prompt)
            loader = FinnhubLoader(
                symbols=params.get("symbols", []),
                query=prompt,
                category=params.get("category"),
                from_date=params.get("from_date"),
                to_date=params.get("to_date")
            )
            # Load data from Finnhub API using extracted parameters
            loader.df = loader.load_headlines()
            # Apply AI filtering to ensure date exclusivity
            matching_records = loader.run_with_natural_language(prompt)
            
            # Convert stock symbols to company names in the data
            if not matching_records.empty:
                data_list = matching_records.to_dict('records')
                converted_data = convert_symbols_to_company_names_in_data(data_list)
                matching_records = pd.DataFrame(converted_data)
        except Exception as e:
            # Fallback to CSV if AI extraction fails
            loader = CSVLoader("data/headlines.csv")
            matching_records = loader.run_with_natural_language(prompt)
            
            # Convert stock symbols to company names in the data
            if not matching_records.empty:
                data_list = matching_records.to_dict('records')
                converted_data = convert_symbols_to_company_names_in_data(data_list)
                matching_records = pd.DataFrame(converted_data)

    if matching_records.empty:
        return pd.DataFrame(), 0

    return matching_records, len(matching_records)


def summarise_single_headline(headline_data: dict) -> NewsSummaryResponse:
    """Summarise a single headline on demand.
    
    Args:
        headline_data: Dictionary containing headline information
        
    Returns:
        NewsSummaryResponse: AI-generated summary
    """
    record_with_context = add_article_context([headline_data])
    result = ask_for_strict_news_summary(record_with_context)
    return result


def main() -> None:
    """Streamlit app main function."""
    import streamlit as st
    st.title("Market Pulse - AI News Summariser")
    st.markdown("Search and summarise financial news using AI-powered natural language processing.")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Settings")
        data_source = st.selectbox("Data Source", ["Finnhub API", "CSV File"], index=0)
        
        if data_source == "Finnhub API":
            st.markdown("### Finnhub Configuration")
            st.info("AI will extract stock symbols and date range from your natural language search query.")
            csv_path = None
            symbols = None
            category = None
        else:
            st.markdown("### CSV Configuration")
            csv_path = st.text_input("CSV Path", value="data/headlines.csv")
            symbols = None
            category = None
    
    # Initialize session state
    if "query" not in st.session_state:
        st.session_state.query = ""
    if "headlines_df" not in st.session_state:
        st.session_state.headlines_df = pd.DataFrame()
    if "total_records" not in st.session_state:
        st.session_state.total_records = 0
    if "summaries" not in st.session_state:
        st.session_state.summaries = {}
    if "generating_summaries" not in st.session_state:
        st.session_state.generating_summaries = set()
    
    # Main search interface
    st.header("News Search")
    
    with st.form("search_form"):
        query = st.text_input(
            "Enter your search query",
            placeholder="e.g., 'Apple news from July' or 'Tesla AI announcements'",
            value=st.session_state.query,
            key="search_input"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            search_button = st.form_submit_button("Search", type="primary")
        with col2:
            clear_button = st.form_submit_button("Clear")
    
    if clear_button:
        st.session_state.query = ""
        st.session_state.headlines_df = pd.DataFrame()
        st.session_state.total_records = 0
        st.session_state.summaries = {}
        st.session_state.generating_summaries = set()
        st.rerun()
    
    # Search and display headlines
    if search_button and query:
        st.session_state.query = query
        st.session_state.summaries = {}  # Clear summaries on new search
        
        with st.spinner("Searching for headlines..."):
            try:
                # Parse symbols if provided
                symbols_list = [s.strip().upper() for s in symbols.split(",")] if symbols else None
                
                headlines_df, total_records = search_headlines(
                    query, 
                    csv_path if csv_path else None,
                    symbols_list,
                    category
                )
                st.session_state.headlines_df = headlines_df
                st.session_state.total_records = total_records
                
                if headlines_df.empty:
                    st.warning("No matching headlines found for your query.")
                else:
                    st.success(f"Found {total_records} headlines.")
                    
            except ValueError as e:
                st.error(f"Error: {str(e)}")
            except RuntimeError as e:
                st.error(f"API Error: {str(e)}")
                st.error("Please check your API key configuration.")
            except Exception as e:
                st.error(f"Unexpected error: {str(e)}")
                import traceback
                st.error(f"Traceback: {traceback.format_exc()}")
    
    # Display headlines with Steam-style pagination
    if not st.session_state.headlines_df.empty:
        st.subheader(f"Headlines ({st.session_state.total_records} total)")
        
        # Steam-style pagination
        items_per_page = 10
        total_pages = (st.session_state.total_records + items_per_page - 1) // items_per_page
        
        if "current_page" not in st.session_state:
            st.session_state.current_page = 1
        
        # Page navigation
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("← Previous", disabled=st.session_state.current_page == 1):
                st.session_state.current_page -= 1
                st.rerun()
        with col2:
            st.write(f"Page {st.session_state.current_page} of {total_pages}")
        with col3:
            if st.button("Next →", disabled=st.session_state.current_page == total_pages):
                st.session_state.current_page += 1
                st.rerun()
        
        # Display headlines for current page
        start_idx = (st.session_state.current_page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, st.session_state.total_records)
        page_headlines = st.session_state.headlines_df.iloc[start_idx:end_idx]
        
        for idx, row in page_headlines.iterrows():
            headline_id = row.get('id', idx)
            
            # Check if this headline is currently being summarised
            is_this_being_summarised = headline_id in st.session_state.generating_summaries
            
            with st.container():
                # Headline card
                st.markdown(f"### {row.get('headline', 'No headline')}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Company:** {row.get('company', 'N/A')}")
                with col2:
                    st.write(f"**Date:** {row.get('date', 'N/A')}")
                with col3:
                    st.write(f"**Source:** {row.get('source', 'N/A')}")
                
                if 'url' in row and pd.notna(row['url']):
                    st.markdown(f"[Read full article]({row['url']})")
                
                # Summarise button
                has_summary = headline_id in st.session_state.summaries
                
                if st.button("Summarise", key=f"summarise_{headline_id}", disabled=has_summary or is_this_being_summarised):
                    st.session_state.generating_summaries.add(headline_id)
                    st.session_state[f"headline_data_{headline_id}"] = row.to_dict()
                    st.rerun()
                
                # Show generation status (no blocking here)
                if is_this_being_summarised:
                    st.markdown("""
                        <div style="display: flex; align-items: center; gap: 8px; padding: 10px; background-color: #f0f2f6; border-radius: 4px; margin: 10px 0;">
                            <div style="border: 3px solid #f3f3f3; border-top: 3px solid #3498db; border-radius: 50%; width: 20px; height: 20px; animation: spin 1s linear infinite;"></div>
                            <span style="color: #0d47a1; font-weight: 500;">Generating summary...</span>
                        </div>
                        <style>
                        @keyframes spin {
                            0% { transform: rotate(0deg); }
                            100% { transform: rotate(360deg); }
                        }
                        </style>
                    """, unsafe_allow_html=True)
                
                # Show error if any
                if f"error_{headline_id}" in st.session_state:
                    st.markdown(f"""
                        <div style="padding: 10px; background-color: #ffebee; border-radius: 4px; margin: 10px 0; color: #c62828;">
                            ❌ Error generating summary: {st.session_state[f"error_{headline_id}"]}
                        </div>
                    """, unsafe_allow_html=True)
                    del st.session_state[f"error_{headline_id}"]
                
                # Display summary if available
                if headline_id in st.session_state.summaries:
                        summary = st.session_state.summaries[headline_id]
                        with st.expander("AI Summary", expanded=True):
                            for item in summary.news:
                                st.markdown(f"**Summary:** {item.summary}")
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Expected Price Direction", item.expected_price_direction)
                                with col2:
                                    st.metric("Company Impact", item.company_impact)
                                st.markdown(f"**Impact Reasoning:** {item.impact_reasoning}")
                
                st.markdown("---")
        
        # Page navigation at bottom
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("← Previous", key="bottom_prev", disabled=st.session_state.current_page == 1):
                st.session_state.current_page -= 1
                st.rerun()
        with col2:
            st.write(f"Page {st.session_state.current_page} of {total_pages}")
        with col3:
            if st.button("Next →", key="bottom_next", disabled=st.session_state.current_page == total_pages):
                st.session_state.current_page += 1
                st.rerun()
    
    # Process all pending summaries at the end (after all rendering)
    if st.session_state.generating_summaries:
        for headline_id in list(st.session_state.generating_summaries):
            if f"headline_data_{headline_id}" in st.session_state:
                try:
                    headline_data = st.session_state[f"headline_data_{headline_id}"]
                    summary = summarise_single_headline(headline_data)
                    st.session_state.summaries[headline_id] = summary
                    st.session_state.generating_summaries.discard(headline_id)
                    del st.session_state[f"headline_data_{headline_id}"]
                except Exception as e:
                    st.session_state[f"error_{headline_id}"] = str(e)
                    st.session_state.generating_summaries.discard(headline_id)
                    del st.session_state[f"headline_data_{headline_id}"]
        
        # Rerun to show the completed summaries
        st.rerun()


if __name__ == "__main__":
    main()


__all__ = [
    "CSVLoader",
    "NewsSummaryResponse",
    "ask_question",
    "ask_for_strict_news_summary",
    "search_headlines",
    "summarise_single_headline",
    "main",
]
