# News data

`headlines.csv` is the input for the project. It uses these columns:

- `id`: a unique row identifier
- `company`: the company the headline concerns
- `date`: publication date, ideally `YYYY-MM-DD`
- `headline`: the news headline to analyse
- `source`: where the headline came from
- `url`: a link to the original item

The rows currently included are a small real-world example so that the project has something to inspect on day one. Before the week, replace them with a 50-100 row export from [Finnhub Company News](https://finnhub.io/docs/api/company-news), using the same columns. That export is supplied to the student as a local file; fetching live news is optional stretch work, not part of the core project.

Financial news is context, not investment advice. The app must not make price predictions or trading recommendations.
