import openai
import os
from my_libs.common.logger import Log
from my_libs.common.bucket_storage import BucketStorage
from my_libs.common.firestore_document import FireStoreDocument
import concurrent.futures
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

    def generate2D(self, prompt: str, size_override = None, additional_suffixes = []) -> str:
        Log.debug("generate2D: " + str(prompt))
        response = openai.Image.create(
            prompt=prompt + 
            " " + Generator.__visual_generation_config["suffix"] + 
            " " + " ".join(additional_suffixes),
            n=1,
            size=size_override or str(Generator.__visual_generation_config["size"]),
        )
        image_url = response['data'][0]['url']
        Log.debug("generate2D: done")
        Log.debug("host image...")
        image_url = Generator.__bucket_storage.fetch_and_host_image(image_url)
        Log.debug(f"host image: done ({image_url})")
        return image_url
    
    def generate2DwithMetadata(self, prompt, size_override = None, additional_suffixes = []):
        return {
            'image_url': self.generate2D(prompt, size_override, additional_suffixes),
            'image_description': prompt
        }

    def generate2Dconcurrent(self, prompts, size_override=None, additional_suffixes=[]):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(self.generate2DwithMetadata, prompts, [size_override] * len(prompts), [additional_suffixes] * len(prompts)))
        return results