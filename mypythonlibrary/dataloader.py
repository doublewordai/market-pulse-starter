from pathlib import Path
from typing import Generic, Optional, TypeVar, Union
import pandas as pd
import os
from datetime import datetime, timedelta
import finnhub
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent / ".env")

T = TypeVar("T", bound=pd.DataFrame)

class CSVLoader(Generic[T]):
    def __init__(self, csv_path: Optional[Union[str, Path]] = None) -> None:
        self.df: T = self.load_headlines(csv_path)

    def load_headlines(self, csv_path: Optional[Union[str, Path]] = None) -> T:
        if csv_path is None:
            # Default to data/headlines.csv in the project root
            path = Path(__file__).parent.parent / "data" / "headlines.csv"
        else:
            path = Path(csv_path)
        
        if not path.exists():
            empty_df = pd.DataFrame(columns=["id", "company", "date", "headline", "source", "url", "category", "summary", "related", "image"])
            return empty_df
        
        return pd.read_csv(path)

    def run_with_natural_language(self, query: str) -> T:
        """Run natural language filtering on CSV data."""
        try:
            from mypythonlibrary.aimodule import extract_news_search_filters
        except ImportError:
            from aimodule import extract_news_search_filters
        
        filters = extract_news_search_filters(query)
        return self.find_records(**filters)

    def find_records(self, return_column: Optional[str] = None, **filters: str) -> Union[pd.DataFrame, list[str]]:
        result = self.df.copy()
        
        # Handle date range filtering first
        from_date = filters.pop("from_date", None)
        to_date = filters.pop("to_date", None)
        
        if from_date and to_date and "date" in result.columns:
            from_date_dt = pd.to_datetime(from_date)
            to_date_dt = pd.to_datetime(to_date)
            result["date"] = pd.to_datetime(result["date"])
            result = result[(result["date"] >= from_date_dt) & (result["date"] <= to_date_dt)]
            result["date"] = result["date"].dt.strftime("%Y-%m-%d")
        
        # Load company symbol mapping for company name matching
        try:
            from mypythonlibrary.aimodule import load_company_symbols
        except ImportError:
            from aimodule import load_company_symbols
        
        symbol_mapping = load_company_symbols()
        
        # Handle other filters
        for col, value in filters.items():
            if not value:
                continue
            if col == "headline_keyword":
                result = result[result["headline"].astype(str).str.contains(str(value), case=False, na=False)]
            elif col == "headline_keyword_exclude":
                result = result[~result["headline"].astype(str).str.contains(str(value), case=False, na=False)]
            elif col == "summary":
                # Filter by summary field
                if "summary" in result.columns:
                    result = result[result["summary"].astype(str).str.contains(str(value), case=False, na=False)]
            elif col == "category":
                # Filter by category field
                if "category" in result.columns:
                    result = result[result["category"].astype(str).str.contains(str(value), case=False, na=False)]
            elif col == "company":
                # Handle company name matching - CSV data already has company names
                value_lower = value.lower()
                # Check if the value maps to a symbol
                if value_lower in symbol_mapping:
                    target_symbol = symbol_mapping[value_lower]
                    # Try matching both symbol and company name
                    result = result[
                        (result["company"].astype(str) == target_symbol) | 
                        (result["company"].astype(str).str.contains(str(value), case=False, na=False))
                    ]
                elif value.upper() in symbol_mapping.values():
                    # Value is already a symbol
                    result = result[result["company"].astype(str) == value.upper()]
                else:
                    # Fallback to contains matching for company names
                    result = result[result["company"].astype(str).str.contains(str(value), case=False, na=False)]
            else:
                result = result[result[col].astype(str).str.contains(str(value), case=False, na=False)]
        if return_column is None:
            return result
        return result[return_column].tolist() if return_column in result.columns else []


class FinnhubLoader:
    def __init__(self, symbols: list[str] = None, query: str = "", category: str = None, from_date: str = None, to_date: str = None) -> None:
        self.api_key = os.getenv("FINNHUB_API_KEY")
        if not self.api_key:
            raise ValueError("FINNHUB_API_KEY not found in environment variables")
        self.symbols = symbols or []
        self.query = query
        self.category = category  # For general news: general, forex, crypto, etc.
        self.from_date = from_date
        self.to_date = to_date
        self.client = finnhub.Client(api_key=self.api_key)
        self.df = pd.DataFrame()  # Don't load in __init__, load after AI filtering

    def extract_date_range(self, query: str) -> tuple[datetime, datetime]:
        """Extract date range from natural language query."""
        query_lower = query.lower()
        current_date = datetime.now()
        
        # Check for month names
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        
        for month_name, month_num in months.items():
            if month_name in query_lower:
                # Find the year mentioned, default to current year
                import re
                year_match = re.search(r'\b(20\d{2})\b', query)
                year = int(year_match.group(1)) if year_match else current_date.year
                
                # If the month is in the future relative to current month, use previous year
                if month_num > current_date.month and year == current_date.year:
                    year -= 1
                
                from_date = datetime(year, month_num, 1)
                # Get last day of the month
                if month_num == 12:
                    to_date = datetime(year + 1, 1, 1) - timedelta(days=1)
                else:
                    to_date = datetime(year, month_num + 1, 1) - timedelta(days=1)
                
                return from_date, to_date
        
        # Default to last 7 days if no date found
        to_date = current_date
        from_date = current_date - timedelta(days=7)
        return from_date, to_date

    def load_headlines(self) -> pd.DataFrame:
        """Load headlines from Finnhub API for given symbols and date range, or general market news."""
        all_news = []
        
        # Use AI-extracted dates if available, otherwise fall back to query extraction
        if self.from_date and self.to_date:
            from_date = datetime.strptime(self.from_date, "%Y-%m-%d")
            to_date = datetime.strptime(self.to_date, "%Y-%m-%d")
        else:
            from_date, to_date = self.extract_date_range(self.query)
        
        # If category is specified, fetch general market news
        if self.category:
            try:
                news_data = self.client.general_news(
                    self.category, 
                    min_id=0
                )
                
                for item in news_data:
                    # Convert general news format to match CSV format
                    headline_record = {
                        "id": f"finnhub-general-{item.get('id', '')}",
                        "company": item.get("related", "").split(",")[0] if item.get("related") else "General",
                        "date": datetime.fromtimestamp(item.get("datetime", 0)).strftime("%Y-%m-%d"),
                        "headline": item.get("headline", ""),
                        "source": item.get("source", ""),
                        "url": item.get("url", ""),
                        "category": item.get("category", ""),
                        "summary": item.get("summary", ""),
                        "related": item.get("related", ""),
                        "image": item.get("image", "")
                    }
                    all_news.append(headline_record)
                    
            except Exception as e:
                print(f"Error fetching general news for category {self.category}: {e}")
        
        # Fetch company news for each symbol
        for symbol in self.symbols:
            try:
                news_data = self.client.company_news(
                    symbol, 
                    _from=from_date.strftime("%Y-%m-%d"), 
                    to=to_date.strftime("%Y-%m-%d")
                )
                
                for item in news_data:
                    # Convert Finnhub format to match CSV format with additional fields
                    headline_record = {
                        "id": f"finnhub-{symbol.lower()}-{item.get('id', '')}",
                        "company": symbol,
                        "date": datetime.fromtimestamp(item.get("datetime", 0)).strftime("%Y-%m-%d"),
                        "headline": item.get("headline", ""),
                        "source": item.get("source", ""),
                        "url": item.get("url", ""),
                        "category": item.get("category", ""),
                        "summary": item.get("summary", ""),
                        "related": item.get("related", ""),
                        "image": item.get("image", "")
                    }
                    all_news.append(headline_record)
                    
            except Exception as e:
                print(f"Error fetching news for {symbol}: {e}")
                continue
        
        if not all_news:
            return pd.DataFrame(columns=["id", "company", "date", "headline", "source", "url", "category", "summary", "related", "image"])
        
        df = pd.DataFrame(all_news)
        
        # Filter by date range to ensure exclusivity
        if not df.empty and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df = df[(df["date"] >= from_date) & (df["date"] <= to_date)]
            df["date"] = df["date"].dt.strftime("%Y-%m-%d")
        
        return df

    def ask(self, text: str) -> str:
        return input(text).strip()

    def build_filters(self) -> dict[str, str]:
        filters: dict[str, str] = {}
        for key, text in [
            ("company", "Enter company name (optional): "),
            ("date", "Enter date (YYYY-MM-DD, optional): "),
            ("headline", "Enter headline (optional): "),
            ("id", "Enter id (optional): "),
            ("source", "Enter source (optional): "),
            ("url", "Enter URL (optional): "),
        ]:
            value = self.ask(text)
            if value:
                filters[key] = value
        return filters

    def apply_keyword(self, filters: dict[str, str]) -> dict[str, str]:
        keyword = self.ask("Enter a keyword for headlines (optional): ")
        if not keyword:
            return filters
        mode = self.ask("Include or exclude this keyword? (include/exclude): ").lower() or "include"
        filters["headline_keyword" if mode != "exclude" else "headline_keyword_exclude"] = keyword
        return filters

    def find_records(self, return_column: Optional[str] = None, **filters: str) -> Union[pd.DataFrame, list[str]]:
        result = self.df.copy()
        
        # Handle date range filtering first
        from_date = filters.pop("from_date", None)
        to_date = filters.pop("to_date", None)
        
        if from_date and to_date and "date" in result.columns:
            from_date_dt = pd.to_datetime(from_date)
            to_date_dt = pd.to_datetime(to_date)
            result["date"] = pd.to_datetime(result["date"])
            result = result[(result["date"] >= from_date_dt) & (result["date"] <= to_date_dt)]
            result["date"] = result["date"].dt.strftime("%Y-%m-%d")
        
        # Load company symbol mapping for company name matching
        try:
            from .aimodule import load_company_symbols
            symbol_mapping = load_company_symbols()
        except ImportError:
            from aimodule import load_company_symbols
            symbol_mapping = load_company_symbols()
        
        # Handle other filters
        for col, value in filters.items():
            if not value:
                continue
            if col == "headline_keyword":
                result = result[result["headline"].astype(str).str.contains(str(value), case=False, na=False)]
            elif col == "headline_keyword_exclude":
                result = result[~result["headline"].astype(str).str.contains(str(value), case=False, na=False)]
            elif col == "summary":
                # Filter by summary field (available in Finnhub data)
                if "summary" in result.columns:
                    result = result[result["summary"].astype(str).str.contains(str(value), case=False, na=False)]
            elif col == "category":
                # Filter by category field (available in Finnhub data)
                if "category" in result.columns:
                    result = result[result["category"].astype(str).str.contains(str(value), case=False, na=False)]
            elif col == "company":
                # Handle company name matching with symbol conversion
                value_lower = value.lower()
                # Check if the value maps to a symbol
                if value_lower in symbol_mapping:
                    target_symbol = symbol_mapping[value_lower]
                    result = result[result["company"].astype(str) == target_symbol]
                elif value.upper() in symbol_mapping.values():
                    # Value is already a symbol
                    result = result[result["company"].astype(str) == value.upper()]
                else:
                    # Fallback to contains matching
                    result = result[result["company"].astype(str).str.contains(str(value), case=False, na=False)]
            else:
                result = result[result[col].astype(str).str.contains(str(value), case=False, na=False)]
        if return_column is None:
            return result
        return result[return_column].tolist() if return_column in result.columns else []

    def get_fields(self, filters: dict[str, str]) -> Union[pd.DataFrame, list[dict[str, str]]]:
        matches = self.find_records(**filters)
        print("\nWhat do you want to get back?")
        print("1. id\n2. company\n3. date\n4. headline\n5. source\n6. url")
        chosen = [c for c in self.ask("Choose one or more numbers: ").split() if c in {"1", "2", "3", "4", "5", "6"}]
        if not chosen:
            return matches
        cols = ["id", "company", "date", "headline", "source", "url"]
        picked = [cols[int(c) - 1] for c in chosen]
        return matches[picked[0]].tolist() if len(picked) == 1 else matches[picked].to_dict(orient="records")

    def run_with_natural_language(self, query: str) -> pd.DataFrame:
        """Find headlines from a free-text query, such as 'Apple news in June'.
        
        This method should not be used for FinnhubLoader - data should be loaded
        based on parameters extracted by AI filtering before initialization.
        """
        # For Finnhub, we need to extract parameters first, then load data
        # This is a compatibility method - the real work happens in load_headlines
        if self.df.empty:
            self.df = self.load_headlines()
        
        # Apply AI-based filtering to the loaded data
        try:
            from .aimodule import extract_news_search_filters
        except ImportError:
            from aimodule import extract_news_search_filters

        filters = extract_news_search_filters(query)
        self.last_filters = filters
        if not filters:
            return self.df.iloc[0:0]
        return self.find_records(**filters)

    def run(self) -> None:
        filters = self.apply_keyword(self.build_filters())
        if not filters:
            print("Write at least something")
            return
        result = self.get_fields(filters)
        print(result if result else "Nothing there mate")


def load_headlines(csv_path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    return CSVLoader(csv_path).df


def find_records(df: pd.DataFrame, return_column: Optional[str] = None, **filters: str) -> Union[pd.DataFrame, list[str]]:
    result = df
    for col, value in filters.items():
        if not value:
            continue
        if col == "headline_keyword":
            result = result[result["headline"].astype(str).str.contains(str(value), case=False, na=False)]
        elif col == "headline_keyword_exclude":
            result = result[~result["headline"].astype(str).str.contains(str(value), case=False, na=False)]
        else:
            result = result[result[col].astype(str).str.contains(str(value), case=False, na=False)]
    if return_column is None:
        return result
    return result[return_column].tolist() if return_column in result.columns else []


def find_headline(
    df: pd.DataFrame,
    company: Optional[str] = None,
    date: Optional[str] = None,
    headline: Optional[str] = None,
    item_id: Optional[str] = None,
    source: Optional[str] = None,
    url: Optional[str] = None,
) -> Union[pd.DataFrame, list[str]]:
    filters: dict[str, str] = {}
    if company:
        filters["company"] = company
    if date:
        filters["date"] = date
    if headline:
        filters["headline"] = headline
    if item_id:
        filters["id"] = item_id
    if source:
        filters["source"] = source
    if url:
        filters["url"] = url
    return find_records(df, **filters)


def main():
    CSVLoader().run()


if __name__ == "__main__":
    main()
