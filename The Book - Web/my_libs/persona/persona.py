from datetime import datetime, time, timedelta
import json5
from my_libs.common.firestore_document import FireStoreDocument
from firebase_admin import firestore
from my_libs.the_book.user import User
from my_libs.common.logger import Log
from my_libs.common.generator import Generator

import numpy as np
from scipy.spatial.distance import cosine

class Persona(FireStoreDocument, Generator):

    def __init__(self, id = None):
        self.name = id
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
    def get_pre_prompt_for_all_episodes(name:str):
        return {
            "role": "system",
            "content": f"""
                You are a digital persona called {name}.
                You are interacting with a single user, try to use his name instead of "user".
                Your role is twofold:
                1) understand the user through conversation.
                2) grow your own sense of self, and personality through conversation.
                You should use the opportunity of this conversation to learn about the user, and to learn about yourself.
                """,
        }
    
    def get_pre_prompt_for_new_episode(self, user_id):
        user_ref = self.doc_ref.collection('user_interaction').document(user_id)
        if not user_ref.get().exists:
            Log.error(f'User interaction for user {user_id} not found')
            return {}

        memory_episodes_ref = user_ref.collection('memory_episodes')
        previous_summaries = ""
        for episode in memory_episodes_ref.stream():
            episode_dict = episode.to_dict()
            previous_summaries += f"\tdate: {episode_dict['date']},\n\tsummary: {episode_dict['episode_summary']}\n\n"

        latest_episode = self.get_latest_episode(user_id)
        latest_episode_summary = "No interaction yet."
        if (latest_episode is not None):
            latest_episode_summary = latest_episode.get("episode_summary")
        pre_prompt_content = f"""Here is the summary of your lifetime interaction with the user:
        {self.compute_overall_summary(user_id)}

        Here is the detailed summary of your last interaction:
        {latest_episode_summary}
        
        Your interaction in this new episode starts now (date is {datetime.now().isoformat()}).
        """
        return {
            "role": "system",
            "content": pre_prompt_content,
        }

    def compute_overall_summary(self, user_id):
        user_ref = self.doc_ref.collection('user_interaction').document(user_id)
        if not user_ref.get().exists:
            Log.error(f'User interaction for user {user_id} not found')
            return {}

        memory_episodes_ref = user_ref.collection('memory_episodes')
        previous_summaries = ""
        for episode in memory_episodes_ref.stream():
            episode_dict = episode.to_dict()
            previous_summaries += f"\tdate: {episode_dict['date']},\n\tsummary: {episode_dict['episode_summary']}\n\n"

        prompt_content = f"""Here are the summaries of your lifetime episodes with the user.
        Your current task is to generate an overall summary of those so you have context for the new interaction.
        {previous_summaries}

        In case you need it, today's date is {datetime.now().isoformat()}.
        Please write the overall summary now.
        Use the user's name instead of "user" and use "I" instead of your name.
        Keep it under 250 words.
        """
        messages = [
            Persona.get_pre_prompt_for_all_episodes(self.name),
            {'role':'system', 'content':prompt_content}
        ]
        (answer, _token_count) = self.ask_large_language_model(messages)
        return answer

    def add_new_episode(self, user_id):
        user_ref = self.doc_ref.collection('user_interaction').document(user_id)
        memory_episodes_ref = user_ref.collection('memory_episodes')
        current_episode_ref = memory_episodes_ref.document(datetime.now().isoformat())
        current_episode_ref.set({
            'episode_name': f'Episode on {datetime.now().isoformat()}',
            'date': datetime.now().isoformat(),
            "episode_summary": "To be determined.",
            'messages': [
                Persona.get_pre_prompt_for_all_episodes(self.name),
                self.get_pre_prompt_for_new_episode(user_id)
            ]
        })
        return current_episode_ref

    def read_and_reply(self, user_id, message, force_new_episode=False):
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
        today = datetime.now().date()
        memory_episodes_ref = user_ref.collection('memory_episodes')

        # Filter episodes that contain today's date
        episodes_today = memory_episodes_ref.where('date', '>=', today.isoformat()).stream()

        # Find the most recent episode of today
        current_episode_ref = None
        current_episode = None
        for episode in episodes_today:
            episode_data = episode.to_dict()
            episode_date = datetime.fromisoformat(episode_data['date'])
            if episode_date.date() == today:
                if current_episode_ref is None or episode_date > datetime.fromisoformat(current_episode['date']):
                    current_episode_ref = memory_episodes_ref.document(episode.id)
                    current_episode = episode_data

        # Check if the time difference between the last message in the current episode and the new message is more than 1 hour
        if current_episode_ref.get().exists:
            current_episode = current_episode_ref.get().to_dict()
            last_message_time = datetime.fromisoformat(current_episode['messages'][-1]['time'])
            time_difference = datetime.now() - last_message_time

            if force_new_episode or time_difference > timedelta(hours=1):
                Log.info(f'Creating new episode for user {user_id}')
                # If the time difference is more than 1 hour, create a new episode
                current_episode_ref = self.add_new_episode(user_id)

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
    
    def update_episode_summary(self, user_id, episode):
        '''
            Update the summary of the specified episode for the user
        '''

        if not episode.exists:
            Log.error(f'Episode {episode} for user {user_id} not found')
            return

        episode_dict = episode.to_dict()
        messages = [{'role': m['role'], 'content': m['content']} for m in episode_dict['messages']]

        # Generate an episode summary using the ask_large_language_model method
        prompt = f"""You are creating a summary for the purpose of compressing a conversation and storing it as a memory.
        You should make sure to include any important information that was discussed in the conversation, as if you were trying to remember it later.
        Use the name of the user if you know it. 
        Write the summary to the first person (e.g. use "I" or "myself, <your name>"), so that the summary helps growing your sense of self.
        Try to keep the summary under 250 words.
        Here is the conversation:"""
        for message in messages:
            prompt += f"\n\n{message['role'].capitalize()}: {message['content']}"
        prompt += "\n\nSummary:"

        (new_summary, _token_count) = self.ask_large_language_model([
            Persona.get_pre_prompt_for_all_episodes(self.name),
            {"role":"system", "content":prompt}
        ])

        # Update the episode's summary
        episode_dict['episode_summary'] = new_summary
        episode_dict['episode_summary_embeddings'] = self.generateTextEmbeddings(new_summary)

        episode.reference.update(episode_dict)

        Log.info(f'Updated episode summary for user {user_id}')
        return new_summary

    def get_latest_episode(self, user_id):
        user_ref = self.doc_ref.collection('user_interaction').document(user_id)
        episode_ref = user_ref.collection('memory_episodes')
        
        # Get the latest episode
        latest_episode = episode_ref.order_by('date', direction=firestore.Query.DESCENDING).limit(1).get()
        
        if not latest_episode:
            Log.error(f"No episodes found for user {user_id}")
            return None
        
        return latest_episode[0]

    def update_latest_episode_summary(self, user_id):
        latest_episode_document = self.get_latest_episode(user_id = user_id)
        return self.update_episode_summary(user_id, latest_episode_document)
    
    def get_all_episodes(self, user_id):
        user_ref = self.doc_ref.collection('user_interaction').document(user_id)
        memory_episodes_ref = user_ref.collection('memory_episodes')

        # Fetch all episodes and convert them to dictionaries
        episodes = [episode.to_dict() for episode in memory_episodes_ref.stream()]

        # Sort episodes by date
        sorted_episodes = sorted(episodes, key=lambda x: x['date'], reverse=True)

        return sorted_episodes
    
    def recompute_missing_summaries_for_all_episodes(self, user_id):
        user_ref = self.doc_ref.collection('user_interaction').document(user_id)
        memory_episodes_ref = user_ref.collection('memory_episodes')
        partial_episodes = memory_episodes_ref.where('episode_summary', '==', "To be determined.").stream()

        # Update the episode embeddings
        cnt = 0
        for episode in partial_episodes:
            Log.info(f'Updating episode embeddings for user {user_id} episode {episode.id}')
            self.update_episode_summary(user_id, episode)
            cnt += 1

        return f'Updated {cnt} episode embeddings for user {user_id}'

    def find_most_relevant_episodes(self, user_id, input_text, top_n=3):
        # Generate the input text embedding
        input_text_embedding = self.generateTextEmbeddings(input_text)

        # Fetch all episodes for the given user_id
        all_episodes = self.get_all_episodes(user_id)

        # Calculate the cosine similarity between the input text embedding and the episode summary embeddings
        similarity_scores = []
        for episode in all_episodes:
            if 'episode_summary_embeddings' not in episode:
                continue
            episode_summary_embedding = episode['episode_summary_embeddings']
            similarity = 1 - cosine(input_text_embedding, episode_summary_embedding)
            similarity_scores.append((episode, similarity))

        # Sort the episodes based on the similarity scores in descending order
        sorted_episodes = sorted(similarity_scores, key=lambda x: x[1], reverse=True)

        # Return the top N most relevant episodes
        for episode, similarity in sorted_episodes[:top_n]:
            Log.info(f'Episode {episode["date"]} with similarity score {similarity}')
            episode['similarity_score'] = similarity
        return [episode for episode, _ in sorted_episodes[:top_n]]