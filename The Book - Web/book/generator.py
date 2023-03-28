import openai
import os
from book.logger import Log
from book.bucket_storage import BucketStorage
from book.firestore_document import FireStoreDocument
openai.api_key = os.getenv("OPENAI_API_KEY")

class Generator:
    __bucket_storage = None
    __visual_generation_config = None
    __llm_config = None

    def __init__(self) -> None:
        if Generator.__bucket_storage is None:
            Generator.__bucket_storage = BucketStorage()

        if Generator.__visual_generation_config is None:
            Generator.__visual_generation_config = FireStoreDocument('configurations','image_generation').getDict()
            Log.info(f"Visual generation config: {Generator.__visual_generation_config}")
        
        if Generator.__llm_config is None:
            Generator.__llm_config = FireStoreDocument('configurations', 'large_language_model').getDict()
            Log.info(f"llm config: {Generator.__llm_config}")

    def ask_large_language_model(self, messages):
        Log.debug("ask_large_language_model...")
        chat_completion = openai.ChatCompletion.create(
            model=Generator.__llm_config['model'],
            messages=messages,
            max_tokens=Generator.__llm_config['max_tokens'],
        )
        Log.debug("ask_large_language_model... done")
        return (chat_completion.choices[0].message.content, chat_completion.usage["total_tokens"])
    
    def generate2D(self, prompt: str) -> str:
        Log.debug("generate2D: " + prompt)
        response = openai.Image.create(
            prompt=prompt + " " + Generator.__visual_generation_config["suffix"],
            n=1,
            size=str(Generator.__visual_generation_config["size"]),
        )
        image_url = response['data'][0]['url']
        Log.debug("generate2D: done")
        Log.debug("host image...")
        image_url = Generator.__bucket_storage.fetch_and_host_image(image_url)
        Log.debug(f"host image: done ({image_url})")
        return image_url