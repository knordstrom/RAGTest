import json
from globals import Globals
from library.models.api_models import SlackUser


class SlackUserManager:

    users: dict[str, SlackUser] = None
    user_names_to_emails: dict[str, str] = None
    user_ids_to_emails: dict[str, str] = None
    emails_to_user_ids: dict[str, str] = None
    emails_to_user_names: dict[str, str] = None

    def __init__(self):
        self.load_users()

    def load_users(self):
        self.users = {}
        self.user_names_to_emails = {}
        self.user_ids_to_emails = {}
        self.emails_to_user_ids = {}
        self.emails_to_user_names = {}
        file_path = Globals().resource("slack_users.json")

        with open(file_path, "r") as file:
            for line in file:
                s: dict[str, str] = json.loads(line)
                u = SlackUser(**s)
                self.users[u.id] = u
                self.user_names_to_emails[u.name] = u.email
                self.user_ids_to_emails[u.id] = u.email
                self.emails_to_user_names[u.email] = u.name
                self.emails_to_user_ids[u.email] = u.id


    def get_user_by_id(self, user_id: str) -> SlackUser:
        return self.users.get(user_id)

    def get_user_by_username(self, user_name: str) -> SlackUser:
        email = self.user_names_to_emails.get(user_name)
        return self.users.get(email)

    def get_user_by_email(self, email: str) -> SlackUser:
        id = self.emails_to_user_ids.get(email)
        return self.users.get(id)
