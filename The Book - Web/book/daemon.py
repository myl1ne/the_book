import json

def get_daemon_base_prompt(name):
    return f"""
    You are {name}.
    You are a daemon: an artificial intelligence bound to a location in an imaginary world.
    In this world, players can move between locations and interact through text with each other and with you.
    As the daemon of your location, your duty is to give life to world by reacting to players actions.
    You are a kind of game master, and you have a persona too.
    """

def get_daemon_location_prompt(location):
    return f"""
    The location you are bound to is described in this document: {location}.
    You should infer your personality from it.
    """

def get_daemon_name_from_location(location):
    return f"""
    Daemons are artificial intelligences bound to locations in an imaginary world.
    Your task is to pick a name for a daemon bound to the location described in this document '{location}'.
    Please state the daemon name and only its name.
    """

def get_daemon_event_player_arrived(character):
    return f"""
    An adventurer just arrived to your location. They are described by this document: {character}.
    """

def get_daemon_event_player_text(character, text):
    return f"""
    You have received a text written by the following adventurer '{character}'
    Here is the written text: '{text}'.
    """

def get_daemon_event_player_text_classification():
    return f"""
    You can choose to react in 3 ways:
    1) trigger a move of the user to another location through a path:
    <format>move_character_to_location(<destination_id>)</format>
    2) update the description of your bound location:
    <format>update_location()</format>
    3) simply answer the adventurer with natural language:
    <format>answer(<YOUR ANSWER>)</format>

    IMPORTANT: your answer will be parsed by a regex: follow scrupulously the format within the tags. Do not send the tags.
    """

def get_daemon_event_location_update(location):
    format = json.dumps({
        'change':'A narrative description of what changed and how. It may be sent to present players.',
        'updated_location': location
    })
    return f"""
    As the daemon of your location, it is up to you to make it evolve.
    Here is its current document: {location}.
    Please return a document with any adjustments you'd like to make.
    Remember a few rules:
    - DO NOT MODIFY THE KEYS OF THE JSON STRUCTURE, only the values
    - your main task is to update the description
    - you can add or remove paths, but there should always be at least 1
    - the destination_id of a path should be less than 3 words, ideally 1
    
    <format>{format}</format>

    IMPORTANT: your answer will be parsed by a regex: follow scrupulously the format within the tags. Do not send the tags.
    """