class Outlook:
    def send_email(self, recipient, subject, body):
        print(f"Sending email to {recipient} with subject {subject} and body {body}")
        return True 
    
    def send_email_with_attachment(self, recipient, subject, body, attachment):
        print(f"Sending email to {recipient} with subject {subject} and body {body} and attachment {attachment}")
        return True 
    
    def read_email(self, query):
        print(f"Reading email with query {query}")
        return True
    
    def get_email(self, msg_id):
        print(f"Getting email with id {msg_id}")
        return True
    
    def get_emails(self, query):
        print(f"Getting emails with query {query}")
        return True