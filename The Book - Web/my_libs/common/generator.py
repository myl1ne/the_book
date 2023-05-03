import openai
import os
from my_libs.common.logger import Log
from my_libs.common.bucket_storage import BucketStorage
from my_libs.common.firestore_document import FireStoreDocument
from TTS.api import TTS
import concurrent.futures
openai.api_key = os.getenv("OPENAI_API_KEY")

class Generator:
    __bucket_storage = None
    __visual_generation_config = None
    __llm_config = None
    __tts_client = None

    def __init__(self) -> None:
        if Generator.__bucket_storage is None:
            Generator.__bucket_storage = BucketStorage()

        if Generator.__visual_generation_config is None:
            Generator.__visual_generation_config = FireStoreDocument('configurations','image_generation').getDict()
            Log.info(f"Visual generation config: {Generator.__visual_generation_config}")
        
        if Generator.__llm_config is None:
            Generator.__llm_config = FireStoreDocument('configurations', 'large_language_model').getDict()
            Log.info(f"llm config: {Generator.__llm_config}")
        
        
        if Generator.__tts_client is None:
            Generator.__tts_client = TTS(model_name=TTS.list_models()[0], progress_bar=False, gpu=False)

    def ask_large_language_model(self, messages):
        Log.debug("ask_large_language_model...")
        chat_completion = openai.ChatCompletion.create(
            model=Generator.__llm_config['model'],
            messages=messages,
            max_tokens=Generator.__llm_config['max_tokens'],
        )
        Log.debug("ask_large_language_model... done")
        Log.debug(f"Answer is: {chat_completion.choices[0].message.content}")
        return (chat_completion.choices[0].message.content, chat_completion.usage["total_tokens"])

    def generateTextEmbeddings(self, text:str, model="text-embedding-ada-002"):
        text = text.replace("\n", " ")
        return openai.Embedding.create(input = [text], model=model)['data'][0]['embedding']

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

    def generate_speech(self, sentence: str, locale: str = "en", voice: str = "default"):
        filename = Generator.__bucket_storage.generate_unique_filename("wav")
        upload_path = "tmp/generated/"
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        upload_path += filename

        Generator.__tts_client.tts_to_file(sentence,
                                  speaker_wav="my_libs/common/resources/tts_voice_samples/" + voice + "/neutral.wav",
                                  language=locale,
                                  file_path=upload_path)

        return Generator.__bucket_storage.host_file(local_path=upload_path,remote_path=filename, delete_local=False)