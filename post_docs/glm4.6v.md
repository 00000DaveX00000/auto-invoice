from zai import ZhipuAiClient
import base64

client = ZhipuAiClient(api_key="your-api-key")  # 填写您自己的APIKey

img_path = "your/path/xxx.png"
with open(img_path, "rb") as img_file:
    img_base = base64.b64encode(img_file.read()).decode("utf-8")

response = client.chat.completions.create(
    model="glm-4.6v",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": img_base
                    }
                },
                {
                    "type": "text",
                    "text": "请描述这个图片"
                }
            ]
        }
    ],
    thinking={
        "type": "enabled"
    }
)
print(response.choices[0].message)