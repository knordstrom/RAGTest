import datetime
import io
import json
import os
import dotenv
from slack_sdk import WebClient
from google.oauth2.credentials import Credentials
from slack_sdk.oauth import AuthorizeUrlGenerator
import datetime

from library.utils import Utils

class Slack:
    users = {}
    user_names_to_emails = {
        "keith": "keith@cognimate.ai",
        "aditham": "prakash@cognimate.ai",
        "mshash": "mithali@cognimate.ai",
        "pradeepjavangula": "pradeep@cognimate.ai",
    }
    user_ids_to_emails = {
        "U06EP4STTQ8": "keith@cognimate.ai",
        "U06E2R1AYCU": "prakash@cognimate.ai",
        "U06J697E08Y": "mithali@cognimate.ai",
        "U06DKQZ2J4F": "pradeep@cognimate.ai"
    }

    @property
    def emails_to_user_ids(self):
        return {v: k for k, v in self.user_ids_to_emails.items()}
    
    @property
    def emails_to_user_names(self):
        return {v: k for k, v in self.user_names_to_emails.items()}

    token_file = "slack_token.json"
    bot_token_file = "slack_bot_token.json"
    def __init__(self):
        dotenv.load_dotenv()
        self.client_id = os.getenv("SLACK_CLIENT_ID")
        self.client_secret = os.getenv("SLACK_CLIENT_SECRET")
        
        self.oauth_scope = [
            "users:read",
            #"users:read.history",
            # "links.read",
            # "files.read",
            # "groups.read",
        ]
        self.oauth_user_scope = [
            "channels:history", 
            "channels:read", 
            #"email", 
            # "files:read", 
            # "groups:read", 
            # "im:history", 
            # "links:read", 
            # "mpim:read", 
            # "reactions:read", 
            # "remote_files:read", 
            # "usergroups:read"
        ]
        self.client = WebClient()
        self.bot_client = None

    def api_test(self):
        response = self.client.api_test()
        return response

    def auth_test(self):
        response = self.client.auth_test()
        return response
    
    def get_conversations(self):
        response = self.client.conversations_list(
            types="public_channel, private_channel"
        )
        return response
    
    def auth_target(self, state):

        authorize_url_generator = AuthorizeUrlGenerator(
            client_id= self.client_id,
            scopes=self.oauth_scope,
            user_scopes=self.oauth_user_scope
        )
        url = authorize_url_generator.generate(state)
        print("URL: ", url)
        return url
         
    
    def check_auth(self):
        creds = None
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.oauth_user_scope)
            if not creds.expired:
                self.client = WebClient(token=creds.token)
        return creds
    
    def check_bot_auth(self):
        creds = None
        if os.path.exists(self.bot_token_file):
            creds = Credentials.from_authorized_user_file(self.bot_token_file, self.oauth_scope)

        if not creds.expired:
            self.bot_client = WebClient(token=creds.token)
        else:
            raise SlackAuthException("Bot creds expired")
            print("Bot creds expired")
        
        return creds
    
    def finish_auth(self, auth_code):
        # verify state received in params matches state we originally sent in auth request
        #if received_state == state:
            # Excha`nge the authorization code for an access token with Slack
        response = self.client.oauth_v2_access(
            client_id=self.client_id,
            client_secret=self.client_secret,
            code=auth_code
        )
        token = response.data.get("authed_user",{}).get("access_token")
        print("Response: ", response.data)
        print("Initial Token: ", token)


        print("Expires in: ", response.data.get("authed_user",{}).get("expires_in"))
        formatted = {
            "token": response.data.get("authed_user",{}).get("access_token"),
            "refresh_token": response.data.get("authed_user",{}).get("refresh_token"),
           # "token_uri": "https://oauth2.googleapis.com/token", 
            "client_id": self.client_id, 
            "client_secret": self.client_secret, 
            "scopes": response.data.get("authed_user",{}).get("scope").split(","), 
            "account": "", 
            "expiry": (datetime.datetime.now() + datetime.timedelta(seconds=response.data.get("authed_user",{}).get("expires_in"))).isoformat()
        }

        with open(self.token_file, "w") as save_file:
             print("Writing to file", self.token_file," ", formatted)
             json.dump(formatted, save_file)
        print("Saved to file, responding")
        return response.data
    
    def read_conversations(self):
        response = self.client.conversations_list()
        conversations = response.data

        result = []
        for convo in conversations.get('channels', []):
            channel = self.process_channel(convo)

            messages = self.read_messages(convo.get('id'))

            threads = []
            for message in messages:
                thread_id =  f"{channel.get('id')}|{message.get('ts')}"
                try:
                    replies = self.client.conversations_replies(channel=convo.get('id'), ts=message.get('ts'))
                    print(len(replies.data.get('messages', [])), " replies found for ", convo.get('id'), message.get('ts'))
                    thread = {
                        "id": thread_id,
                        "messages": []
                    }
                    for reply in replies.data.get('messages', []):
                        thread["messages"].append(self.process_message(reply))
                    threads.append(thread)
                except Exception as e:
                    print("Replies not found with", convo.get('id'), message.get('ts'))
                    threads.append({
                        "id": thread_id,
                        "messages" : [self.process_message(message)]
                    })
            print("     Adding ", len(threads), " threads to ", channel.get('name'))
                
            channel['threads'] = threads
            result.append(channel)

        return result
    
    user_keep_keys = ["id", "name", "real_name", "email", "deleted", "is_bot"]
    message_keep_keys = ["user", "text", "ts", "reactions", "reply_users"]
    
    def get_user(self, user_id):
        if not self.bot_client:
            self.check_bot_auth()
        if user_id in self.users:
            user = self.users[user_id]
        else:
            response = self.bot_client.users_info(user=user_id)
            user = response.data.get("user", {})
            user['email'] = self.user_ids_to_emails.get(user_id, "")
            self.users[user_id] = user

        return Utils.dict_keep_keys(user, ["id", "name", "real_name", "email", "deleted", "is_bot"])
    
    def read_messages(self, channel_id):
        response = self.client.conversations_history(channel=channel_id)
        messages = response.data.get("messages", [])
        for message in messages:
            self.process_message(message)
        return messages
    
    def process_channel(self, channel):
        print(channel.keys())
        return Utils.dict_keep_keys(channel, ['id', 'name', 'creator', 'is_private', 'is_shared', 'num_members', 'updated'])
    
    def process_message(self, message):
        response = Utils.dict_keep_keys(message, ["user", "text", "ts", "attachments", "type", "subtype"])
        user = self.get_user(message.get('user'))
        response['email'] = user['email']
        attachments = message.get("attachments", [])
        if attachments:
            response['attachments'] = self.process_attachments(attachments)
        return response

    def process_attachments(self, attachments):
        return Utils.array_keep_keys(attachments, ["fallback", "from_url", "id", "original_url", "text", "title", "ts"])
    

class SlackAuthException(Exception):
    pass