from pathlib import Path
from typing import Generic, Optional, TypeVar, Union
import pandas as pd

# class Finnhub(ABC):
#     """Abstract class for generic data handling."""
#     @abstractmethod
#     def load_data(self):
#         """Load data from a source."""
#         pass

#     @abstractmethod
#     def get_by_id(self, id: str):
#         """Get object by id."""
#         pass

#     @abstractmethod
#     def search_by_filters(self, **filters):
#         """Get search objects by filters."""
#         pass

# class APILoader(Finnhub):
#     def __init__(self, api_key):
#         self.api_key = api_key

T = TypeVar("T", bound=pd.DataFrame)

class CSVLoader(Generic[T]):
    def __init__(self, csv_path: Optional[Union[str, Path]] = None) -> None:
        self.df: T = self.load_headlines(csv_path)

    def load_headlines(self, csv_path: Optional[Union[str, Path]] = None) -> T:
        path = Path(__file__).with_name("headlines.csv") if csv_path is None else csv_path
        return pd.read_csv(path)

    def ask(self, text: str) -> str:
        return input(text).strip()

    def build_filters(self) -> dict[str, str]:
        filters: dict[str, str] = {}
        for key, text in [("company", "Enter company name (optional): "), ("date", "Enter date (YYYY-MM-DD, optional): "), ("headline", "Enter headline (optional): "), ("id", "Enter id (optional): ")]:
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

    def find_records(self, return_column: Optional[str] = None, **filters: str) -> Union[T, list[str]]:
        result = self.df
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

    def get_fields(self, filters: dict[str, str]) -> Union[T, list[dict[str, str]]]:
        matches = self.find_records(**filters)
        print("\nWhat do you want to get back?")
        print("1. id\n2. company\n3. date\n4. headline")
        chosen = [c for c in self.ask("Choose one or more numbers: ").split() if c in {"1", "2", "3", "4"}]
        if not chosen:
            return matches
        cols = ["id", "company", "date", "headline"]
        picked = [cols[int(c) - 1] for c in chosen]
        return matches[picked[0]].tolist() if len(picked) == 1 else matches[picked].to_dict(orient="records")

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
    return find_records(df, **filters)


def main():
    CSVLoader().run()


if __name__ == "__main__":
    main()