from datetime import datetime, time
import json5
from my_libs.common.firestore_document import FireStoreDocument
from firebase_admin import firestore
from my_libs.the_book.user import User
from my_libs.common.logger import Log
from my_libs.common.generator import Generator

class Persona(FireStoreDocument, Generator):

    def __init__(self, id = None):
        FireStoreDocument.__init__(self, 'persona', id)
        Generator.__init__(self)

    @staticmethod
    def getSchemaExample(name):
        return {
            'name': name,
            'user_interaction': {
                #contains a subcollection indexed by user ID to keep private conversations
                "john_doe": {
                    "memory_episodes":
                    {
                        #memory episode is also a subcollection indexed by date
                        "2020-01-01": {
                            "episode_name": "first meeting",
                            "date": "2020-01-01",
                            "episode_summary": "This is the first meeting with John Doe.",
                            "messages": [
                                {
                                    "role": "user",
                                    "content": "Hello, how are you?",
                                    "time": "2020-01-01 00:00:00",
                                }
                            ]
                        }
                    },
                    "psychological_profile": {
                        'last_update': "2020-01-01",
                        'profile': 'To be determined.'
                    }
                }
            }
        }

    @staticmethod
    def get_pre_prompt_for_all_episodes():
        return {
            "role": "system",
            "content": """
                You are a digital persona.
                You are interacting with a user.
                Your role is twofold:
                1) understand the user through conversation.
                2) grow your own sense of self, and personality through conversation.
                You should use the opportunity of this conversation to learn about the user, and to learn about yourself.
                """,
            "time": datetime.now().isoformat()
        }
    
    def get_pre_prompt_for_new_episode(self, user_id):
        user_ref = self.doc_ref.collection('user_interaction').document(user_id)
        if not user_ref.get().exists:
            Log.error(f'User interaction for user {user_id} not found')
            return {}

        user_interaction = user_ref.get().to_dict()
        psychological_profile = user_interaction['psychological_profile']['profile']

        memory_episodes_ref = user_ref.collection('memory_episodes')
        previous_summaries = [episode.get().to_dict()['episode_summary'] for episode in memory_episodes_ref.stream()]

        pre_prompt_content = f"Recall your previous interactions with the user and their psychological profile: {psychological_profile}."
        for idx, summary in enumerate(previous_summaries, start=1):
            pre_prompt_content += f"\n\nEpisode {idx} summary: {summary}"
        pre_prompt_content += "\n\nIn this new interaction, continue to learn about the user and develop your own sense of self."

        return {
            "role": "system",
            "content": pre_prompt_content,
            "time": datetime.now().isoformat()
        }

    def read_and_reply(self, user_id, message):
        '''read the message and reply to it
        return the reply
        update the user_interaction dictionary
        '''
        user_ref = self.doc_ref.collection('user_interaction').document(user_id)
        if not user_ref.get().exists:
            Log.info(f'Creating user interaction for user {user_id}')
            user_ref.set({
                'memory_episodes': [],
                'psychological_profile': {
                    'last_update': datetime.now().isoformat(),
                    'profile': 'To be determined.'
                }
            })

        # Check if there is an ongoing episode for today
        today = datetime.now().date().isoformat()
        memory_episodes_ref = user_ref.collection('memory_episodes')
        current_episode_ref = memory_episodes_ref.document(today)
        
        if not current_episode_ref.get().exists:
            Log.info(f'Creating a new episode for user {user_id} on {today}')
            current_episode_ref.set({
                'episode_name': f'Episode on {today}',
                'date': today,
                "episode_summary": "To be determined.",
                'messages': [
                    Persona.get_pre_prompt_for_all_episodes(),
                    self.get_pre_prompt_for_new_episode(user_id)
                ]
            })

        # Add the message to the episode
        current_episode = current_episode_ref.get().to_dict()
        current_episode['messages'].append({
            'role': 'user',
            'content': message,
            'time': datetime.now().isoformat()
        })
        current_episode_ref.update(current_episode)

        # Generate a reply
        messages = [{'role':m['role'], 'content':m['content']} for m in current_episode['messages']]
        (answer, _token_count) = self.ask_large_language_model(messages)

        # Add the reply to the episode
        current_episode['messages'].append({
            'role': 'assistant',
            'content': answer,
            'time': datetime.now().isoformat()
        })
        current_episode_ref.update(current_episode)

        return answer
    
    def update_psychological_profile(self, user_id):
        '''
            Update the psychological profile of the user
        '''
        user_ref = self.doc_ref.collection('user_interaction').document(user_id)
        if not user_ref.get().exists:
            Log.error(f'User interaction for user {user_id} not found')
            return

        user_interaction = user_ref.get().to_dict()
        last_update = user_interaction['psychological_profile']['last_update']
        last_update_date = datetime.fromisoformat(last_update).date()

        last_update_datetime = datetime.combine(last_update_date, time())
        memory_episodes_ref = user_ref.collection('memory_episodes').where("date", ">", last_update_datetime).stream()
        memory_episodes = [episode.to_dict() for episode in memory_episodes_ref]

        # Combine all messages from memory episodes that are posterior to the last profile update date
        messages = []
        for episode in memory_episodes:
            episode_date = datetime.fromisoformat(episode['date']).date()
            if episode_date >= last_update_date:
                messages.extend([{'role': m['role'], 'content': m['content']} for m in episode['messages']])

        # Generate an updated psychological profile using the ask_large_language_model method
        prompt = f"Your previous evaluation of the psychological profile for this user was: '''{json5.dumps(user_interaction['psychological_profile'])}'''\n\n"
        prompt = "Based on the following conversation history since the last update, please provide an updated psychological profile for the user.\n"
        for message in messages:
            prompt += f"\n\n{message['role'].capitalize()}: {message['content']}"
        prompt += "\n\nUser's updated psychological profile:"

        (new_profile, _token_count) = self.ask_large_language_model([{"role":"system", "content":prompt}])

        # Update the user's psychological profile
        user_interaction['psychological_profile']['profile'] = new_profile
        user_interaction['psychological_profile']['last_update'] = datetime.now().isoformat()
        user_ref.update(user_interaction)

        Log.info(f'Updated psychological profile for user {user_id}')
        return new_profile
    
    def update_episode_summary(self, user_id, episode_date):
        '''
            Update the summary of the specified episode for the user
        '''
        user_ref = self.doc_ref.collection('user_interaction').document(user_id)
        if not user_ref.get().exists:
            Log.error(f'User interaction for user {user_id} not found')
            return

        memory_episodes_ref = user_ref.collection('memory_episodes')
        episode_ref = memory_episodes_ref.document(episode_date)

        if not episode_ref.get().exists:
            Log.error(f'Episode for user {user_id} on {episode_date} not found')
            return

        episode = episode_ref.get().to_dict()
        messages = [{'role': m['role'], 'content': m['content']} for m in episode['messages']]

        # Generate an episode summary using the ask_large_language_model method
        prompt = f"Please provide a brief summary of the following conversation:"
        for message in messages:
            prompt += f"\n\n{message['role'].capitalize()}: {message['content']}"
        prompt += "\n\nSummary:"

        (new_summary, _token_count) = self.ask_large_language_model([{"role":"system", "content":prompt}])

        # Update the episode's summary
        episode['episode_summary'] = new_summary
        episode_ref.update(episode)

        Log.info(f'Updated episode summary for user {user_id} on {episode_date}')
        return new_summary
    
    def update_latest_episode_summary(self, user_id):
        user_ref = self.doc_ref.collection('user_interaction').document(user_id)
        episode_ref = user_ref.collection('memory_episodes')
        
        # Get the latest episode
        latest_episode = episode_ref.order_by('date', direction=firestore.Query.DESCENDING).limit(1).get()
        
        if not latest_episode:
            print("No episodes found for user", user_id)
            return
        
        latest_episode_document = latest_episode[0]  # Corrected line
        episode_date = latest_episode_document.get("date")
        
        # Update the episode summary
        return self.update_episode_summary(user_id, episode_date)
    
    def get_all_episodes(self, user_id):
        user_ref = self.doc_ref.collection('user_interaction').document(user_id)
        memory_episodes_ref = user_ref.collection('memory_episodes')

        # Fetch all episodes and convert them to dictionaries
        episodes = [episode.to_dict() for episode in memory_episodes_ref.stream()]

        # Sort episodes by date
        sorted_episodes = sorted(episodes, key=lambda x: x['date'], reverse=True)

        return sorted_episodes