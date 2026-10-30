import os
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

client = OpenAI(
    api_key=os.environ["llm7_api"],
    base_url="https://api.llm7.io/v1",
)
messages: list[ChatCompletionMessageParam] = [{"role": "system", "content": "You are a helpful assistant."}]
while True:
    inp = input(">")
    messages.append({"role": "user", "content": inp})
    response = client.chat.completions.create(
        model="default",
        messages=messages,
        stream=False,
    )
    answer = response.choices[0].message.content or ""
    messages.append({"role": "assistant", "content": answer})
    print(answer)