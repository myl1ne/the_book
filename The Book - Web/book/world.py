from book.firestore_document import FireStoreDocument
from book.generator import Generator
from book.logger import Log
import json5

def world_initialize():
    '''
    This is an admin method that should be called only once.
    It reads the world configuration from the file system and
    adds details about the world.
    '''
    world = FireStoreDocument('configurations','world')
    world_dict = world.getDict()
    gen = Generator()

    expanded_world = FireStoreDocument('worlds')
    expanded_world.set({})

    messages = []

    messages.append(
        {
        "role":"system",
        "content": 
        f"""
        Your role is to add details to an imaginary world.
        This world will be the theater of a text-based game played on internet.
        You will be the creator and administrator of this world.
        """
    })

    messages.append(
        {
        "role":"system",
        "content": 
        f"""
        The world is described as this: '{world_dict['description']}'.
        The atmosphere is '{world_dict['atmosphere']}'.
        The expected audience of players is '{world_dict['audience']}'.
        """
    })
    messages.append(
        {
        "role":"system",
        "content": 
        """
        Your first task is to pick a name for yourself.
        Remember that you are the creator of this world.
        Please answer with the following format:
        {
            "name": "your name",
            "description": "a short description of yourself"
        }
        """
    })

    (answer, tokens) = gen.ask_large_language_model(messages)
    Log.info(f'answer: {answer}')
    expanded_world.update({"creator" : json5.loads(answer)})
    messages.append({"role":"assistant","content": answer})
    #----------------------------------------------
    messages.append(
        {
        "role":"system",
        "content": 
        """
        Your next task is to build a theogony for this world.
        Please answer with the god's name, a short description of the god, and a short description of the god's domain.
        Don't hesitate to create relationships between the gods (e.g. son of, sister of, etc...).
        You can also populate the pantheon with heroes.

        Use the following format:
        [
            {
                "name": "name of the god",
                "description": "a short description of the god, its powers, and its personality",
                "domain": "a short description of the god's domain"
            },
            ...
        ]
        """
    })

    (answer, tokens) = gen.ask_large_language_model(messages)
    Log.info(f'answer: {answer}')
    expanded_world.update({"pantheon" : json5.loads(answer)})
    messages.append({"role":"assistant","content": answer})
    #----------------------------------------------
    messages.append(
        {
        "role":"system",
        "content": 
        """
        Your next task is to build a bestiary.
        Imagine the most iconic creatures of this world.
        
        Use the following format:
        [
            {
                "name": "creature name",
                "description": "a short description",
                "legend": "a legend or folklore about this creature"
            },
            ...
        ]
        """
    })

    (answer, tokens) = gen.ask_large_language_model(messages)
    Log.info(f'answer: {answer}')
    expanded_world.update({"bestiary" : json5.loads(answer)})
    messages.append({"role":"assistant","content": answer})
    #----------------------------------------------
    messages.append(
        {
        "role":"system",
        "content": 
        """
        Your next task is to describe the main factions ruling this world.
        
        Use the following format:
        [
            {
                "name": "faction name",
                "description": "a short description",
                "ways": "the ways of those people",
                "relationships": "relations with other factions"
            },
            ...
        ]
        """
    })

    (answer, tokens) = gen.ask_large_language_model(messages)
    Log.info(f'answer: {answer}')
    expanded_world.update({"factions" : json5.loads(answer)})
    messages.append({"role":"assistant","content": answer})
    #----------------------------------------------
    #messages.append(
    #    {
    #    "role":"system",
    #    "content": 
    #    """
    #    Your next task is to build a geography for this world.
    #    Please name the continents, the seas, and other geographic singularities.
    #    You don't need to use any specific for this answer but keep the answer short.
    #    """
    #})
    #(answer, tokens) = gen.ask_large_language_model(messages)
    #Log.info(f'answer: {answer}')
    #expanded_world.update({"geography" : answer})
    #messages.append({"role":"assistant","content": answer})
    #----------------------------------------------
    messages.append(
        {
        "role":"system",
        "content": 
        """
        Your next task is to come up with a 10 facts about this world.
        Please answer with the following format:
        [
            "fact 1",
            "fact 2",
            ...
        ]
        """
    })

    (answer, tokens) = gen.ask_large_language_model(messages)
    Log.info(f'answer: {answer}')
    expanded_world.update({"facts" : json5.loads(answer)})
    messages.append({"role":"assistant","content": answer})
    #----------------------------------------------
    messages.append(
        {
        "role":"system",
        "content": 
        """
        Next you will come up with a general storyline and intrigue
        that the players will be able to follow.

        Please write the text they will receive when they start the game.
        """
    })

    (answer, tokens) = gen.ask_large_language_model(messages)
    Log.info(f'answer: {answer}')
    expanded_world.update({"intrigue" : answer})
    messages.append({"role":"assistant","content": answer})


    #----------------------------------------------
    return expanded_world.getDict()