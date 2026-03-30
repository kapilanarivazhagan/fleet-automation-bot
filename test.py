from openai import OpenAI

client = OpenAI(
    api_key="gsk_YiiXIbQUBGK5vMSzoAuxWGdyb3FY7MIyjCotrVuZf1FRN7yS2t2RE",
    base_url="https://api.groq.com/openai/v1"
)

response = client.chat.completions.create(
    model="llama3-8b-8192",
    messages=[
        {"role": "user", "content": "Say hello"}
    ],
)

print(response.choices[0].message.content)