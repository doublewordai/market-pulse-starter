# market-pulse-starter

## Running the API
The project includes a small FastAPI application exposing headline lookups.
Install dependencies and run the server:

```bash
pip install -r requirements.txt
# from project root
python -m data.app
# or
uvicorn data.api:app --reload --host 127.0.0.1 --port 8000
```

Endpoints:

- `GET /headlines/?company=<name>&date=<YYYY-MM-DD>` — returns matching headlines or 404
- `POST /headlines/` — JSON body `{ "company": "...", "date": "YYYY-MM-DD" }`

# Market Pulse

Build a small AI finance news app over five days.

The app should let someone choose a company, browse its recent news, and read a short AI-generated briefing. The briefing should be based on the supplied headlines and returned in a predictable format so the app can display it clearly.

This is a build week, not a worksheet. Research the libraries and ideas you need, try things, and keep notes on decisions and problems. Ask for help after you have made a reasonable attempt and can explain where you are stuck.

## What success looks like on Friday

You can demo a working app and explain:

- where the news data came from
- how your Python code prepared the data
- how you called Doubleword's API
- how you made the AI response predictable enough for the app
- one thing that worked well and one thing you would improve

## Starting point

- `data/headlines.csv` contains the news data for the project.
- `.env.example` shows the environment variables the project will need. Copy it to `.env` before using the API key.
- `requirements.txt` contains the Python packages you are likely to need.
- `outputs/` is a place to save AI results so the app does not need to make a new API request every time it opens.

You will create the Python files and decide how to organise them as the project develops.

## Suggested tools

- Python for the project code
- Streamlit for the app
- Doubleword's OpenAI-compatible API for the model calls
- CSV and JSON files for storing input and output

## Useful references

- [Doubleword Inference API](https://docs.doubleword.ai/inference-api/intro-to-doubleword-inference)
- [Doubleword API keys](https://docs.doubleword.ai/inference-api/creating-an-api-key)
- [Structured outputs](https://docs.doubleword.ai/inference-api/tool-calling)
- [Streamlit documentation](https://docs.streamlit.io/)

## Ground rules

- Do not put API keys in code or commit them to Git.
- Treat model output as data that needs checking, not as fact.
- Do not build a trading tool or claim to predict share prices.
- Keep the project small enough to finish and demonstrate well.
