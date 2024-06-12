import enum

class KafkaTopics(enum.Enum):
    EMAILS = "emails"
    CALENDAR = "calendar"
    SLACK = "slack"
    DOCUMENTS = "documents"