import enum
from weaviate.classes.config import Property, DataType
import weaviate.classes as wvc

class WeaviateSchemas(enum.Enum):

    EMAIL = 'email'
    EMAIL_TEXT = 'email_text'
    EVENT = 'event'
    EVENT_TEXT = 'event_text'
    DOCUMENT = 'document'
    DOCUMENT_TEXT = 'document_text'
    DOCUMENT_SUMMARY = 'document_summary'
    SLACK_CHANNEL = 'slack_channel'
    SLACK_THREAD = 'slack_thread'
    SLACK_MESSAGE = 'slack_message'
    SLACK_MESSAGE_TEXT = 'slack_message_text'

class WeaviateSchema:

    class_objs: list[(WeaviateSchemas,dict)] = [
        (WeaviateSchemas.EMAIL,{
            "class": "Email",
            "vectorizer": False,

            # Property definitions
            "properties": [
                Property(name = "email_id", data_type=DataType.TEXT),
                Property(name ="history_id", data_type=DataType.TEXT),
                Property(name ="thread_id", data_type=DataType.TEXT),
                Property(name ="labels", data_type=DataType.TEXT_ARRAY),
                Property(name ="to", data_type=DataType.OBJECT_ARRAY, nested_properties=[
                    Property(name ="email", data_type = DataType.TEXT),
                    Property(name ="name", data_type = DataType.TEXT)
                ]),
                Property(name ="cc", data_type=DataType.OBJECT_ARRAY, nested_properties=[
                    Property(name ="email", data_type = DataType.TEXT),
                    Property(name ="name", data_type = DataType.TEXT)
                ]),
                Property(name ="bcc", data_type=DataType.OBJECT_ARRAY, nested_properties=[
                    Property(name ="email", data_type = DataType.TEXT),
                    Property(name ="name", data_type = DataType.TEXT)
                ]),
                Property(name ="subject", data_type=DataType.TEXT),
                Property(name ="from", data_type = DataType.OBJECT, nested_properties=[
                    Property(name ="email", data_type = DataType.TEXT),
                    Property(name ="name", data_type = DataType.TEXT)
                ]),
                Property(name ="date", data_type=DataType.DATE),
            ],          

    }),
    (WeaviateSchemas.EMAIL_TEXT, {
            # Class definition
            "class": "EmailText",

            # Property definitions
            "properties": [
                Property(name = "text", data_type=DataType.TEXT),
                Property(name = "email_id", data_type=DataType.TEXT, description="The weaviate ID of the email this text is associated with (target: Email)"),
                Property(name = "thread_id", data_type=DataType.TEXT, description="An identifier for the thread this email is part of (target: Email)"),              
            ],
            "references": [     

            ],

            # Specify a vectorizer
            "vectorizer": True,
    }),
    (WeaviateSchemas.EVENT, {
            # Class definition
            "class": "Event",

            # Property definitions
            "properties": [
                Property(name = "event_id", data_type=DataType.TEXT),
                Property(name = "summary", data_type=DataType.TEXT),
                Property(name = "location", data_type=DataType.TEXT),
                Property(name = "start", data_type=DataType.DATE),
                Property(name = "end", data_type=DataType.DATE),

                Property(name="email_id", data_type=DataType.TEXT, description="(target: Email)"),
                Property(name="sent_date", data_type=DataType.DATE, description="(target: Email)"),
                Property(name="from", data_type=DataType.TEXT, descriptiondescription="(target: Email)"),
                Property(name="to", data_type=DataType.TEXT, description="(target: Email)"),
                Property(name="thread_id", data_type=DataType.TEXT, description="(target: Email)"),
                Property(name="name", data_type=DataType.TEXT, description="(target: Event)"),
                Property(name="description", data_type=DataType.TEXT, description="(target: Event)"),
            ],
            "references": [
                
            ],

            # Specify a vectorizer
            "vectorizer": False,
    }),
    (WeaviateSchemas.EVENT_TEXT, {
            # Class definition
            "class": "EventText",

            # Property definitions
            "properties": [
                Property(name = "text", data_type=DataType.TEXT),
                Property(name = "event_id", data_type=DataType.TEXT, description="The weaviate ID of the event this text is associated with (target: Event)"),
            ],
            "references": [

            ],

            # Specify a vectorizer
            "vectorizer": True,
    }),
    (WeaviateSchemas.DOCUMENT, {
        "class": "Document",
        "properties": [
            Property(name="document_id", data_type=DataType.TEXT),
           Property(name="metadata", data_type=DataType.OBJECT, nested_properties=[
                Property(name="metadata_id", data_type=DataType.TEXT),
                Property(name="name", data_type=DataType.TEXT),
                Property(name="mimeType", data_type=DataType.TEXT),
                Property(name="viewedByMeTime", data_type=DataType.DATE),
                Property(name="createdTime", data_type=DataType.DATE),
                Property(name="modifiedTime", data_type=DataType.DATE),
                Property(name="owners", data_type=DataType.OBJECT_ARRAY, nested_properties=[
                    Property(name="kind", data_type=DataType.TEXT),
                    Property(name="displayName", data_type=DataType.TEXT),
                    Property(name="photoLink", data_type=DataType.TEXT),
                    Property(name="me", data_type=DataType.BOOL),
                    Property(name="permissionId", data_type=DataType.TEXT),
                    Property(name="emailAddress", data_type=DataType.TEXT)
                ]),
                Property(name="lastModifyingUser", data_type=DataType.OBJECT, nested_properties=[
                    Property(name="kind", data_type=DataType.TEXT),
                    Property(name="displayName", data_type=DataType.TEXT),
                    Property(name="photoLink", data_type=DataType.TEXT),
                    Property(name="me", data_type=DataType.BOOL),
                    Property(name="permissionId", data_type=DataType.TEXT),
                    Property(name="emailAddress", data_type=DataType.TEXT)
            ]),
                Property(name="viewersCanCopyContent", data_type=DataType.BOOL),
                Property(name="permissions", data_type=DataType.OBJECT_ARRAY, nested_properties=[
                    Property(name="kind", data_type=DataType.TEXT),
                    Property(name="permission_id", data_type=DataType.TEXT),
                    Property(name="type", data_type=DataType.TEXT),
                    Property(name="emailAddress", data_type=DataType.TEXT),
                    Property(name="role", data_type=DataType.TEXT),
                    Property(name="displayName", data_type=DataType.TEXT),
                    Property(name="photoLink", data_type=DataType.TEXT),
                    Property(name="deleted", data_type=DataType.BOOL),
                    Property(name="pendingOwner", data_type=DataType.BOOL)
        ]),
        ]),
            Property(name="doc_type", data_type=DataType.TEXT),
        ],
        "references": [

        ],
        "vectorizer": False,
    }),
    (WeaviateSchemas.DOCUMENT_TEXT, {
            # Class definition
            "class": "DocumentText",

            # Property definitions
            "properties": [
                Property(name = "text", data_type=DataType.TEXT),
                Property(name = "document_id", data_type=DataType.TEXT, description="The weaviate ID of the document this text is associated with (target: Document)"),
            ],
            "references": [
            ],

            # Specify a vectorizer
            "vectorizer": True,
    }),
    (WeaviateSchemas.DOCUMENT_SUMMARY, {
            # Class definition
            "class": "DocumentSummary",

            # Property definitions
            "properties": [
                Property(name = "text", data_type=DataType.TEXT),
                Property(name = "document_id", data_type=DataType.TEXT, description="The weaviate ID of the document this text is associated with (target: Document)"),
                Property(name = "document_text_id", data_type=DataType.TEXT, description="The weaviate ID of the document text this summary is associated with (target: DocumentText)"),
            ],
            "references": [
            ],

            # Specify a vectorizer
            "vectorizer": True,
    }),
    (WeaviateSchemas.SLACK_CHANNEL, { 
        "class": "SlackChannel",    

        "properties": [
            Property(name = "channel_id", data_type=DataType.TEXT, description="Unique identifier for the channel"),
            Property(name = "creator", data_type=DataType.TEXT, description="Email address of the creator"),
            Property(name = "name", data_type=DataType.TEXT, description="Name of the channel"),
            Property(name = "is_private", data_type=DataType.BOOL, description="Is the channel private?"),
            Property(name = "is_shared", data_type=DataType.BOOL, description="Is the channel shared?"),
            Property(name = "num_members", data_type=DataType.INT, description="Number of members in the channel"),
            Property(name = "updated", data_type=DataType.DATE, description="Last updated timestamp"),
        ],

        "references": [
        ],

        "vectorizer": False,
    }),
    (WeaviateSchemas.SLACK_THREAD, {  
        "class": "SlackThread",    

        "properties": [
            Property(name = "thread_id", data_type=DataType.TEXT, description="Unique identifier for the thread"),
            Property(name = "channel_id", data_type=DataType.TEXT, description="Unique identifier for the channel (target: SlackChannel)"),
        ],

        "references": [
        ],

        "vectorizer": False,
     }),
    (WeaviateSchemas.SLACK_MESSAGE, {   
            # Class definition
            "class": "SlackMessage",

            # Property definitions
            "properties": [
                Property(name = "message_id", data_type=DataType.TEXT, description="Unique identifier for the message"),
                Property(name = "from", data_type=DataType.TEXT, description="Email address of the sender"),
                Property(name = "subtype", data_type=DataType.TEXT, description="A refinement on the 'type' propeerty of the message"),
                Property(name = "ts", data_type=DataType.TEXT, description="Timestamp of the message"),
                Property(name = "type", data_type=DataType.TEXT, description="Type of the message, usually 'message' or 'file'"),
                Property(name= "thread_id", data_type=DataType.TEXT, description="Unique identifier for the thread (target: SlackThread)"),
            ],
            "references": [
            ],

            # Specify a vectorizer
            "vectorizer": False,
    }),
    (WeaviateSchemas.SLACK_MESSAGE_TEXT, {   
            # Class definition
            "class": "SlackMessageText",

            # Property definitions
            "properties": [
                Property(name = "text", data_type=DataType.TEXT, description="Text content of this chunk of the message"),
                Property(name = "message_id", data_type=DataType.TEXT, description="Unique identifier for the message (target: SlackMessage)"),
                Property(name = "thread_id", data_type=DataType.TEXT, description="Unique identifier for the thread (target: SlackThread)"),
            ],
            "references": [
            ],

            # Specify a vectorizer
            "vectorizer": True,
        })
    ]
    
    class_map = dict(class_objs)

