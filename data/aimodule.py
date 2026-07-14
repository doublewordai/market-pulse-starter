import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class AIClient:

    def __init__(self, api_key: str | None = None, base_url: str = "https://api.doubleword.ai/v1"):
        if api_key is None:
            api_key = (
                os.getenv("DOUBLEWORD_API_KEY")
                or os.getenv("OPENAI_API_KEY")
                or os.getenv("API_KEY")
            )
        self._client = OpenAI(api_key=api_key, base_url=base_url)

    def ask(self, prompt: str, model: str = "deepseek-ai/DeepSeek-V4-Flash", system: str | None = None):
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = self._client.chat.completions.create(model=model, messages=messages)

        try:
            return resp.choices[0].message.content
        except Exception:
            return resp
def ask_question(prompt: str | None = None, **kwargs):
    if prompt is None:
        prompt = input("Enter your message to the AI: ").strip()

    if not prompt:
        raise ValueError("It's not nice to ask the AI nothing. Please provide a prompt.")

    client = AIClient()
    return client.ask(prompt, **kwargs)
if __name__ == "__main__":
    try:
        answer = ask_question()
        print(answer)
    except Exception as e:
        print("Error:", e)