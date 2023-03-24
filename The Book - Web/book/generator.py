import openai
import os
from book.logger import Log
from book.bucket_storage import BucketStorage
openai.api_key = os.getenv("OPENAI_API_KEY")

class Generator:
    __bucket_storage = None

    def __init__(self) -> None:
        if Generator.__bucket_storage is None:
            Generator.__bucket_storage = BucketStorage()

        #Configure parameters for visual pipe
        self.visual_generation_config = {
            'requires_safety_checker': False, 
            'height': 512, 'width': 512, 
            'guidance_scale': 7.5,
            'num_inference_steps': 100
        }

    def ask_large_language_model(self, messages):
        Log.debug("ask_large_language_model...")
        chat_completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        Log.debug("ask_large_language_model... done")
        return (chat_completion.choices[0].message.content, chat_completion.usage["total_tokens"])
    
    def generate2D(self, prompt: str) -> str:
        Log.debug("generate2D: " + prompt)
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size=str(self.visual_generation_config["height"]) + "x" + str(self.visual_generation_config["width"]),
        )
        image_url = response['data'][0]['url']
        Log.debug("generate2D: done")
        Log.debug("host image...")
        image_url = Generator.__bucket_storage.fetch_and_host_image(image_url)
        Log.debug(f"host image: done ({image_url})")
        return image_url