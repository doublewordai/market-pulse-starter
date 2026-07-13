# Mentor Guide

## Aim

The student builds a small, presentable AI finance news app with limited supervision. The core teaching goal is independence: they should research, attempt, describe a problem, then ask a focused question.

The required deliverable is a Streamlit app that lets a user select a company and see news plus saved AI-generated briefings. Friday ends with a short demo.

## Before Monday

- Create a Doubleword API key with a modest hard budget.
- Put the key in the student's local `.env`; do not send it in chat or commit it.
- Check that `data/headlines.csv` is present and contains the supplied Finnhub snapshot. Keep the existing column names if you refresh it.
- Check that Python is available and that the student can install the packages in `requirements.txt`.
- Give them the timetable and research questionnaire already in this folder's parent directory.

## How to supervise

Use short check-ins rather than continuous pairing. A useful rhythm is a 10-minute morning brief, a 10-minute mid-afternoon review, and a short end-of-day handover.

When they are stuck, ask for: what they expected, what happened, the smallest relevant code or error, and what they already tried. Help them isolate the next step; do not take over the implementation.

Keep a running list of deferred ideas. The app should remain focused on company news and AI briefings, not price prediction, trading, databases, deployment, or live data collection.

## Daily guide

### Monday: Data and project footing

Target: the student can load the CSV, inspect rows and columns, list companies, and filter news for one company.

Start by agreeing the data contract: each row represents one headline and includes company, date, headline, source, and URL. Ask them to explain what each field is for before they write much code.

Check-in questions: What is a row? What can be missing or inconsistent? Which company has the most headlines? How would you make filtering reusable?

End-of-day evidence: a small Python script or notebook that loads, prints, filters, and handles an unknown company without crashing.

### Tuesday: First model call

Target: one headline can be sent to Doubleword and the response can be saved locally.

Have them read the current Doubleword inference documentation and find the OpenAI-compatible Python pattern themselves. Give them the API key only once they can explain why it belongs in `.env`.

Check-in questions: What is sent to the model? What response do you get back? What does the error say when the key is missing? What model did you choose and why?

End-of-day evidence: one saved response, plus a script that fails clearly when the API key is absent.

### Wednesday: Constrained, useful output

Target: the model returns a consistent briefing format that the app can read.

Agree a deliberately small result shape, for example: summary, sentiment, confidence, and key themes. The student should write the prompt and decide how their code checks malformed or incomplete output.

Check-in questions: Why is a paragraph hard for an app to use? What is JSON? What would your code do if one field were missing? Which prompt change improved the result?

End-of-day evidence: several saved briefings from different companies, with the same usable structure.

### Thursday: Build the app

Target: a Streamlit app can browse companies, show headlines, and show saved briefings.

Make them sketch the screen on paper first. Keep the interface functional: a company selector, headlines, a briefing, and a source link are enough. Do not permit a model request on every Streamlit refresh.

Check-in questions: What should appear first? What happens when a company has no briefing? Where does the displayed result come from? How will someone tell that the data is real?

End-of-day evidence: a locally running app with the complete core journey.

### Friday: Polish and demo

Target: a reliable, explainable demo.

First run through the core journey from a fresh terminal. Then let the student fix the most visible rough edges, prepare a three-minute explanation, and practise handling two questions.

Suggested demo flow: choose a company, show its headlines and sources, show the AI briefing, explain the data-to-model-to-app path, then name one limitation and one next step.

## Scope control

Core features are local CSV data, realtime Doubleword calls made by a script, saved structured results, and a Streamlit viewer.

Stretch work, only after the core works: compare two prompts, add a simple chart, estimate analysis cost, or replace the supplied CSV using Finnhub's company-news endpoint.

## Ready-for-demo check

- The app starts locally.
- At least three companies have headlines and saved briefings.
- The API key is absent from Git and visible code.
- The student can explain the source of the data and the role of every major part.
- A missing or malformed result does not break the whole app.
