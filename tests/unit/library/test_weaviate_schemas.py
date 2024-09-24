import unittest
from library.models.weaviate_schemas import Document, DocumentSummary, DocumentText, Email, EmailText, EmailThread, Event, EventText, SlackChannel, SlackMessage, SlackMessageText, SlackThread, WeaviateSchemaTransformer
from weaviate.classes.config import Property, DataType

class TestWeaviateSchemas(unittest.TestCase):

    def test_email_thread(self):
        props: list[Property] = WeaviateSchemaTransformer.to_props(EmailThread)
        assert len(props) == 2
        assert props[0] == Property(name = 'thread_id', data_type=DataType.TEXT)
        assert props[1] == Property(name = 'latest', data_type=DataType.DATE)

    def test_email(self):
        props: list[Property] = WeaviateSchemaTransformer.to_props(Email)
        assert len(props) == 12
        assert props[0] == Property(name = 'email_id', data_type=DataType.TEXT)
        assert props[1] == Property(name = 'history_id', data_type=DataType.TEXT)
        assert props[2] == Property(name = 'thread_id', data_type=DataType.TEXT)
        assert props[3] == Property(name = 'labels', data_type=DataType.TEXT_ARRAY)
        assert props[4] == Property(name = 'to', data_type=DataType.OBJECT_ARRAY, 
                                    nested_properties=[
                                        Property(name = 'email', data_type=DataType.TEXT),
                                        Property(name = 'name', data_type=DataType.TEXT)
                                    ])
        assert props[5] == Property(name = 'cc', data_type=DataType.OBJECT_ARRAY, 
                                    nested_properties=[
                                        Property(name = 'email', data_type=DataType.TEXT),
                                        Property(name = 'name', data_type=DataType.TEXT)
                                    ])
        assert props[6] == Property(name = 'bcc', data_type=DataType.OBJECT_ARRAY, 
                                    nested_properties=[
                                        Property(name = 'email', data_type=DataType.TEXT),
                                        Property(name = 'name', data_type=DataType.TEXT)
                                    ])

        assert props[7] == Property(name = 'subject', data_type=DataType.TEXT)
        assert props[8] == Property(name = 'sender', data_type=DataType.OBJECT, nested_properties=[
            Property(name = 'email', data_type=DataType.TEXT),
            Property(name = 'name', data_type=DataType.TEXT)
        ])

        assert props[9] == Property(name = 'date', data_type=DataType.DATE)
        assert props[10] == Property(name = 'provider', data_type=DataType.TEXT)

    def test_email_text(self):
        props: list[Property] = WeaviateSchemaTransformer.to_props(EmailText)
        assert len(props) == 5
        assert props[0] == Property(name = "text", data_type=DataType.TEXT)
        assert props[1] == Property(name = "email_id", data_type=DataType.TEXT)
        assert props[2] == Property(name = "thread_id", data_type=DataType.TEXT)         
        assert props[3] == Property(name = "ordinal", data_type=DataType.INT)
        assert props[4] == Property(name = "date", data_type=DataType.DATE)

    def test_event(self):
        props: list[Property] = WeaviateSchemaTransformer.to_props(Event)
        assert props == [
                Property(name = "event_id", data_type=DataType.TEXT),
                Property(name = "summary", data_type=DataType.TEXT),
                Property(name = "location", data_type=DataType.TEXT),
                Property(name = "start", data_type=DataType.DATE),
                Property(name = "end", data_type=DataType.DATE),
                Property(name="email_id", data_type=DataType.TEXT),
                Property(name="sent_date", data_type=DataType.DATE),
                Property(name="sender", data_type=DataType.TEXT),
                Property(name="to", data_type=DataType.TEXT),
                Property(name="thread_id", data_type=DataType.TEXT),
                Property(name="name", data_type=DataType.TEXT),
                Property(name="description", data_type=DataType.TEXT),
                Property(name ="provider", data_type=DataType.TEXT),
            ]
    
    def test_event_text(self):
        props: list[Property] = WeaviateSchemaTransformer.to_props(EventText)
        assert props == [
                Property(name = "text", data_type=DataType.TEXT),
                Property(name = "event_id", data_type=DataType.TEXT),
                Property(name = "ordinal", data_type=DataType.INT),
            ]
        
    def test_document(self):
        props: list[Property] = WeaviateSchemaTransformer.to_props(Document)
        assert props == [
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
                Property(name ="provider", data_type=DataType.TEXT),
            ]),
            Property(name="doc_type", data_type=DataType.TEXT),
            Property(name="latest", data_type=DataType.DATE),
        ]
    
    def test_document_text(self):
        props: list[Property] = WeaviateSchemaTransformer.to_props(DocumentText)
        assert props == [
            Property(name="text", data_type=DataType.TEXT),
            Property(name="document_id", data_type=DataType.TEXT),
            Property(name="ordinal", data_type=DataType.INT),
        ]
    
    def test_document_summary(self):
        props: list[Property] = WeaviateSchemaTransformer.to_props(DocumentSummary)
        assert props == [
            Property(name="text", data_type=DataType.TEXT),
            Property(name="document_id", data_type=DataType.TEXT),
        ]
    
    def test_slack_channel(self):
        props: list[Property] = WeaviateSchemaTransformer.to_props(SlackChannel)
        assert props ==     [
            Property(name = "channel_id", data_type=DataType.TEXT),
            Property(name = "name", data_type=DataType.TEXT),
            Property(name = "creator", data_type=DataType.TEXT),   
            Property(name = "is_private", data_type=DataType.BOOL),
            Property(name = "is_shared", data_type=DataType.BOOL),
            Property(name = "num_members", data_type=DataType.INT),
            Property(name = "updated", data_type=DataType.DATE),
            Property(name ="provider", data_type=DataType.TEXT),
        ]
    
    def test_slack_thread(self):
        props: list[Property] = WeaviateSchemaTransformer.to_props(SlackThread)
        assert props == [
            Property(name = "thread_id", data_type=DataType.TEXT),
            Property(name = "channel_id", data_type=DataType.TEXT),
            Property(name = "latest", data_type=DataType.DATE),
        ]
    
    def test_slack_message(self):
        props: list[Property] = WeaviateSchemaTransformer.to_props(SlackMessage)
        assert props == [
                Property(name = "message_id", data_type=DataType.TEXT),
                Property(name = "sender", data_type=DataType.TEXT),
                Property(name = "subtype", data_type=DataType.TEXT),
                Property(name = "ts", data_type=DataType.DATE),
                Property(name = "type", data_type=DataType.TEXT),
                Property(name= "thread_id", data_type=DataType.TEXT),
            ]
    
    def test_slack_message_text(self):
        props: list[Property] = WeaviateSchemaTransformer.to_props(SlackMessageText)
        assert props == [
            Property(name = "text", data_type=DataType.TEXT),
            Property(name = "message_id", data_type=DataType.TEXT),
            Property(name = "thread_id", data_type=DataType.TEXT),
            Property(name = "ordinal", data_type=DataType.INT),
        ]