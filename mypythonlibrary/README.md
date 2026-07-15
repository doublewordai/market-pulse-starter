gi# News data

`headlines.csv` is the input for the project. It uses these columns:

- `id`: a unique row identifier; Finnhub's provider ID is combined with the company name because one story can relate to more than one company
- `company`: the company the headline concerns
- `date`: publication date, ideally `YYYY-MM-DD`
- `headline`: the news headline to analyse
- `source`: where the headline came from
- `url`: a link to the original item

## Current snapshot

The supplied data was collected from [Finnhub Company News](https://finnhub.io/docs/api/company-news) on 13 July 2026. It contains 1,486 stories published between 6 and 13 July 2026 for six companies: Apple, Microsoft, NVIDIA, Tesla, Amazon, and Alphabet.

The export is intentionally supplied as a local file. Fetching live news is optional stretch work, not part of the core project. If the dataset is refreshed, record the collection date, coverage dates, companies, and row count here.

Financial news is context, not investment advice. The app must not make price predictions or trading recommendations.
