from openai import OpenAI


c = OpenAI(
    api_key="sk-bD7kBXNausjCQCtM8pbHchuKdtrj581ZxoG78hj8MWO0pn9r",
    base_url="https://api.openai-proxy.org/v1",
)

res = c.completions.create(
    model="gpt-4o-mini",
    prompt="描述一下这张图片 https://resources.xasmc.xyz/backgrounds/bg1.webp",
    max_tokens=100,
)

print(res.choices[0].text)
