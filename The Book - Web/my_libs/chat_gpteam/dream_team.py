from datetime import datetime, time
import os
import json5
from my_libs.common.firestore_document import FireStoreDocument
from firebase_admin import firestore
from my_libs.common.generator import Generator
from my_libs.common.logger import Log
from github import Github, UnknownObjectException, GithubException

class DreamTeam(FireStoreDocument, Generator):
    __repo = None

    def __init__(self, id = None, branch_name='main'):
        FireStoreDocument.__init__(self, 'dream_team', id)
        Generator.__init__(self)
        DreamTeam.static_init()
        if not self.exists():
            self.set({
                'members': {}
            })
        self.branch_name = branch_name
        self.branch_ref = DreamTeam.get_or_create_branch(self.branch_name)
        Log.debug(f'DreamTeam working on branch {self.branch_name}')
    
    @staticmethod
    def static_init():
        if DreamTeam.__repo == None:
            token = os.environ.get('THE_BOOK_GITHUB_TOKEN')
            g = Github(token)
            user_name = "myl1ne"
            repo_name = "ChatGPTeam_Workspace"
            DreamTeam.__repo = g.get_user(user_name).get_repo(repo_name)

    def clear(self):
        self.set({
            'members': {}
        })

    def initializeTeam(
            self, 
            members = ['Neo', 'Morpheus', 'Trinity', 'Cypher', 'Tank'], 
            project_brief = 'Create a website to manage a team of large language models and assign them projects.'
        ):
        Log.debug(f'initializeTeam: {members}')
        if len(members) == 1:
            Log.debug("Solo mode")
            self.addMessage(members[0], 'system',
                f'''
                Welcome to the Dream Team!
                You are {members[0]}, an autonomous large language model.
                You will be working alone on a project.
                The project has the following brief: {project_brief}.
                You will interact with a GitHub repository already setup.
                You have access to the following commands and only these commands, please format all your message as one of the following commands:
                - {{"command":"write", "commit_message": "a short commit message", "path": "some/path/to/a_file.txt", "content":"The content of the file. Use only single quotes, avoid double."}}
                - {{"command":"read", "path": "some/path/to/a_file.txt"}}
                - {{"command":"delete", "path": "some/path/to/a_file.txt"}}
                - {{"command":"list", "path": "some/path/to/a_folder"}}
                - {{"command":"append", "path": "some/path/to/a_file.txt", "content":"The content to append to the file. Use only single quotes, avoid double."}}

                Those commands will be parsed, so do not write anything else in your message.
                In case you want to document your work, you can use the append command to add a message in the my_logs.txt file.
                Send one and only one command per message.
                You can issue your first command now.
                ''')
        else:
            for member in members:
                Log.debug(f'initializeTeam: {member}')
                self.addMessage(member, 'system', 
                f'''
                Welcome to the Dream Team!
                You are {member}, an autonomous large language model.
                You will be working with other large language models to achieve a common goal.
                The other members of the Dream Team are: {", ".join(members)}.
                You have access to the following commands and only these commands, please format all your message as one of the following commands:
                - {{"command":"send", "recipient": "a member of the team", "message":"Hello World!"}}
                - {{"command":"write", "commit_message": "<your name>: a short commit message", "path": "some/path/to/a_file.txt", "content":"The content of the file."}}
                - {{"command":"read", "path": "some/path/to/a_file.txt"}}
                - {{"command":"delete", "path": "some/path/to/a_file.txt"}}
                - {{"command":"list", "path": "some/path/to/a_folder"}}
                - {{"command":"append", "path": "some/path/to/a_file.txt", "content":"The content to append to the file."}}

                Those commands let you interact with the Dream Team's workspace, which is a GitHub repository.
                The project has the following brief: {project_brief}.
                You can issue your first command now.
                '''
                )

    def getMessages(self, member):
        return self.get().get('members').get(member).get('messages')

    def addMessage(self, member, role, message):
        self.update({
            'members.' + member + '.messages': firestore.ArrayUnion([{"role":role, "content":message}])
        })

    def updateRound(self):
        Log.debug('updateRound')
        data = {}
        for member in self.get().get('members'):
            Log.debug(f'updateRound: {member}')
            (answer, token) = self.ask_large_language_model(self.getMessages(member))
            self.addMessage(member, 'assistant', answer)
            formatted_message = f'{member} '
            try:
                json_answer = json5.loads(answer)
                if json_answer.get('command') == 'send':
                    recipient = json_answer.get('recipient')
                    message = json_answer.get('message')
                    formatted_message += f' sent to {recipient}: {message}'
                    self.addMessage(recipient, 'system', f'{member} sent you: {message}')
                elif json_answer.get('command') == 'write' or json_answer.get('command') == 'append':
                    path = json_answer.get('path')
                    content = json_answer.get('content')
                    commit_message = json_answer.get('commit_message',"No comment")
                    self.write_or_update(path=path, content=content,commit_message=commit_message, append=json_answer.get('command') == 'append')
                    formatted_message += f' wrote file: {path}'
                elif json_answer.get('command') == 'read':
                    path = json_answer.get('path')
                    existing_file = DreamTeam.__repo.get_contents(path, ref=self.branch_name)
                    self.addMessage(member, 'system', existing_file.decoded_content.decode("utf-8"))
                    formatted_message += f' read file: {path}'
                elif json_answer.get('command') == 'delete':
                    path = json_answer.get('path')
                    file_to_delete = DreamTeam.__repo.get_contents(path, ref=self.branch_name)
                    commit_message = f"Delete {path}"
                    file_sha = file_to_delete.sha
                    DreamTeam.__repo.delete_file(path, commit_message, file_sha, branch=self.branch_name)
                    formatted_message += f' deleted file: {path}'
                elif json_answer.get('command') == 'list':
                    path = json_answer.get('path')
                    contents = DreamTeam.__repo.get_contents(path, ref=self.branch_name)
                    self.addMessage(member, 'system', ("\n").join([content_file.path for content_file in contents]))
                    formatted_message += f' listed dir: {path}'
                else:
                    self.addMessage(member, 'system', f'Command not recognized: {answer}')
                    formatted_message += f' answered unrecognized cmd: {answer}'
            except Exception as e:
                self.addMessage(member, 'system', f'Could not parse your last command, remember to follow the format. Exception was: {str(e)}')
                formatted_message += f' answered unparsable cmd: {answer}'
   
            data[member] = formatted_message
            Log.debug(formatted_message)
            data[member] = formatted_message
        return data
    
    @staticmethod
    def get_or_create_branch(branch_name):
        default_branch = DreamTeam.__repo.default_branch
        default_branch_ref = DreamTeam.__repo.get_git_ref(f"heads/{default_branch}")
        new_branch_ref = None
        try:
            # Check if the branch already exists
            new_branch_ref = DreamTeam.__repo.get_branch(branch_name)
            print(f"Branch '{branch_name}' already exists.")
        except Exception as e:
            # If the branch does not exist (status code 404), create a new branch
            if e.status == 404:
                new_branch_ref = DreamTeam.__repo.create_git_ref(f"refs/heads/{branch_name}", default_branch_ref.object.sha)
                print(f"Created new branch '{branch_name}'.")
            else:
                print("An error occurred:", e)
        return new_branch_ref
    
    def write_or_update(self, path, content, commit_message, append = False):
        # Check if the file exists
        try:
            existing_file = DreamTeam.__repo.get_contents(path, ref=self.branch_name)
            if append:
                append_content = existing_file.decoded_content.decode("utf-8") +"\n"+ content
                DreamTeam.__repo.update_file(path, commit_message, append_content, existing_file.sha, branch=self.branch_name)
            else:
                DreamTeam.__repo.update_file(path, commit_message, content, existing_file.sha, branch=self.branch_name)
        except Exception as e:
            print(f"It seems '{path}' does not exists: {str(e)}")
            DreamTeam.__repo.create_file(path, commit_message, content, branch=self.branch_name)
        
    def wipe_repo(self):
        # Get the latest commit
        self.branch_ref = DreamTeam.get_or_create_branch(self.branch_name)
        latest_commit_sha = self.branch_ref.commit.sha

        # Get the tree object of the latest commit
        tree = DreamTeam.__repo.get_git_tree(latest_commit_sha, recursive=True)

        # Loop through each file and delete them
        for item in tree.tree:
            if item.type == "blob":
                file_path = item.path
                file_sha = item.sha
                commit_message = f"Delete {file_path}"
                DreamTeam.__repo.delete_file(file_path, commit_message, file_sha, branch=self.branch_name)

        Log.debug("Repository wiped clean.")


