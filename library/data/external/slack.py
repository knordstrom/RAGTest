import datetime
import io
import json
import os
import dotenv
from slack_sdk import WebClient
from google.oauth2.credentials import Credentials
from slack_sdk.oauth import AuthorizeUrlGenerator
import datetime

from slack_sdk.web import SlackResponse
from globals import Globals
from library.enums.data_sources import DataSources
from library.managers.auth_manager import AuthManager
from library.managers.slack_user_manager import SlackUserManager
from library.models.api_models import OAuthCreds, SlackUser
from library.models.employee import User
from library.utils import Utils
import json

class Slack:

    oauth_bot_scope: list[str]
    oauth_user_scope: list[str]
    client: WebClient
    bot_client: WebClient
    user: User
    auth_manager: AuthManager = AuthManager()
    user_manager: SlackUserManager = None

    is_local: bool = False

    token_file: str = Globals().root_resource("slack_token.json")
    bot_token_file: str = Globals().root_resource("slack_bot_token.json")
    def __init__(self, user: User):
        self.user = user
        dotenv.load_dotenv()
        self.is_local = os.getenv("IS_LOCAL") in ["True", "true", "1"]
        self.client_id = os.getenv("SLACK_CLIENT_ID")
        self.client_secret = os.getenv("SLACK_CLIENT_SECRET")
        self.user_manager = SlackUserManager()
        self.oauth_bot_scope = [
            # "users:read",
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

    def api_test(self) -> SlackResponse:
        response: SlackResponse = self.client.api_test()
        return response

    def auth_test(self) -> SlackResponse:
        response: SlackResponse = self.client.auth_test()
        return response
    
    def get_conversations(self) -> SlackResponse:
        response: SlackResponse = self.client.conversations_list(
            types="public_channel, private_channel"
        )
        return response
    
    def auth_target(self, state) -> str:

        authorize_url_generator: AuthorizeUrlGenerator = AuthorizeUrlGenerator(
            client_id= self.client_id,
            scopes=self.oauth_bot_scope,
            user_scopes=self.oauth_user_scope
        )
        url: str = authorize_url_generator.generate(state)
        print("URL: ", url)
        return url
         
    def check_auth(self) -> Credentials:
        return self.check_auth_local() if self.is_local else self.check_auth_deployed()

    def check_auth_local(self) -> Credentials:
        creds = None
        if os.path.exists(self.token_file):
            creds: Credentials = Credentials.from_authorized_user_file(self.token_file, self.oauth_user_scope)
            if not creds.expired:
                self.client = WebClient(token=creds.token)
        return creds
    
    def check_auth_deployed(self) -> Credentials:
        stored_creds: OAuthCreds = self.auth_manager.read_remote_credentials(self.user, DataSources.SLACK)

        if stored_creds:
            creds: Credentials = stored_creds.to_credentials()
            if not creds.expired:
                self.client = WebClient(token=creds.token)
        return creds
    
    def check_bot_auth(self) -> Credentials:
        creds = None
        if os.path.exists(self.bot_token_file):
            creds: Credentials = Credentials.from_authorized_user_file(self.bot_token_file, self.oauth_bot_scope)

        if not creds.expired:
            self.bot_client = WebClient(token=creds.token)
        else:
            raise SlackAuthException("Bot creds expired")
            print("Bot creds expired")
        
        return creds
    
    def finish_auth(self, auth_code: str) -> dict[str, any]:
        # verify state received in params matches state we originally sent in auth request
        #if received_state == state:
            # Excha`nge the authorization code for an access token with Slack
        response: SlackResponse = self.client.oauth_v2_access(
            client_id=self.client_id,
            client_secret=self.client_secret,
            code=auth_code
        )
        token = response.data.get("authed_user",{}).get("access_token")
        print("Response: ", response.data)
        print("Initial Token: ", token)

        print("Expires in: ", response.data.get("authed_user",{}).get("expires_in"))
        if self.is_local:
            self.save_auth_local(response)
        else:
            self.save_auth_deployed(response)

        print("Saved to file, responding")
        return response.data
    
    def save_auth_local(self, response: SlackResponse) -> None:
        formatted: dict[str, str] = {
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

    def save_auth_deployed(self, response: SlackResponse) -> None:
        self.auth_manager \
            .write_remote_credentials(self.user, 
                target = DataSources.SLACK.name, 
                token = response.data.get("authed_user",{}).get("access_token"), 
                refresh_token = response.data.get("authed_user",{}).get("refresh_token"), 
                expiry = (datetime.datetime.now() + datetime.timedelta(seconds=response.data.get("authed_user",{}).get("expires_in"))).isoformat(), 
                client_id = self.client_id, 
                client_secret = self.client_secret, 
                scopes = response.data.get("authed_user",{}).get("scope").split(","))

    def read_conversations(self) -> list[dict[str, any]]:
        response: SlackResponse = self.client.conversations_list()
        conversations: dict[str, any] = response.data

        result: list[dict[str, any]] = []
        convo: dict[str, any]
        for convo in conversations.get('channels', []):
            channel: dict[str, any] = self.process_channel(convo)
            contributor_ids: set[str] = set()

            messages: list[dict[str, any]] = self.read_messages(convo.get('id'))

            threads: list[dict[str, any]] = []
            for message in messages:
                thread_id: str =  f"{channel.get('id')}|{message.get('ts')}"
                try:
                    replies: SlackResponse = self.client.conversations_replies(channel=convo.get('id'), ts=message.get('ts'))
                    print(len(replies.data.get('messages', [])), " replies found for ", convo.get('id'), message.get('ts'))
                    
                    thread_messages: list[dict[str, any]] = []
                    for reply in replies.data.get('messages', []):
                        m: dict[str, any] = self.process_message(reply)
                        contributor_ids.add(m.get('user'))
                        thread_messages.append(m)
                    threads.append({
                        "id": thread_id,
                        "messages": thread_messages
                    })
                except Exception as e:
                    print("Replies not found with", convo.get('id'), message.get('ts'))
                    threads.append({
                        "id": thread_id,
                        "messages" : [self.process_message(message)]
                    })
            print("     Adding ", len(threads), " threads to ", channel.get('name'))
                
            channel['threads'] = threads
            channel['contributors'] = list(contributor_ids)
            result.append(channel)

        return result
    
    # user_keep_keys: list[str] = ["id", "name", "real_name", "email", "deleted", "is_bot"]
    # message_keep_keys: list[str] = ["user", "text", "ts", "reactions", "reply_users"]
    
    # # def get_user(self, user_id: str) -> SlackUser:
    #     # if not self.bot_client:
    #     #     self.check_bot_auth()
    #     # if user_id in self.users:
    #     #     user = self.users[user_id]
    #     # else:
    #     #     response = self.bot_client.users_info(user=user_id)
    #     #     user = response.data.get("user", {})
    #     #     user['email'] = self.user_ids_to_emails.get(user_id, "")
    #     #     self.users[user_id] = user

    def read_messages(self, channel_id: str) -> list[dict[str, any]]:
        response: SlackResponse = self.client.conversations_history(channel=channel_id)
        messages: list[dict[str, any]] = response.data.get("messages", [])
        for message in messages:
            self.process_message(message)
        return messages
    
    def process_channel(self, channel: dict[str, any]) -> dict[str, any]:
        print(channel.keys())
        return Utils.dict_keep_keys(channel, ['id', 'name', 'creator', 'is_private', 'is_shared', 'num_members', 'updated'])
    
    def process_message(self, message: dict[str, any]) -> dict[str, any] :
        response: dict[str, any] = Utils.dict_keep_keys(message, ["user", "text", "ts", "attachments", "type", "subtype"])
        user: SlackUser = self.user_manager.get_user_by_id(message.get('user'))
        response['email'] = user.email if user else ""
        attachments: list[dict[str, any]] = message.get("attachments", [])
        if len(attachments) > 0:
            response['attachments'] = self.process_attachments(attachments)
        return response

    def process_attachments(self, attachments: list[dict[str, any]] ) -> list[dict[str, any]] :
        return Utils.array_keep_keys(attachments, ["fallback", "from_url", "id", "original_url", "text", "title", "ts"])
    

class SlackAuthException(Exception):
    pass