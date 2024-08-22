import copy
import enum
import os
import dotenv
import weaviate as w
#import langchain_experimental.text_splitter as lang_splitter
from langchain_community.embeddings import GPT4AllEmbeddings
from library.models.api_models import DocumentResponse, EmailMessage, EmailThreadResponse, SlackMessage, SlackResponse, SlackThreadResponse, TranscriptConversation, TranscriptLine
from library.data.local.vdb import VDB 
from library import utils
import weaviate.classes as wvc
from weaviate.util import generate_uuid5 as weave_uuid5
from weaviate.classes.config import Property, DataType
from library.models.weaviate_schemas import Email, EmailText, EmailTextWithFrom, WeaviateSchemas, WeaviateSchema
from weaviate.classes.query import Filter
from weaviate.collections.classes.grpc import Sort
from weaviate.collections.collection import Collection
from weaviate.collections.classes.internal import Object
from weaviate.collections.classes.types import Properties, References
from langchain_core.documents import Document
from weaviate.collections.classes.aggregate import AggregateReturn

class Weaviate(VDB):

    host: str
    port: str
    url: str
    schemas = {}
    postponded_references = {}

    _client: w.WeaviateClient = None
    @property
    def client(self) -> w.WeaviateClient:
        if self._client is None:
            print("Connecting to " + self.url)
            self._client = w.connect_to_local(
                host=self.host,
                port=self.port,
            )
        return self._client

    def reset_client(self) -> None:
        self._client = None
        
    def collection(self, key: WeaviateSchemas) -> Collection[Properties, References]:
        schema = self.schemas[key]
        return self.client.collections.get(schema['class'])
    
    def __new__(cls, host = '127.0.0.1', port = '8080', schemas: list[(WeaviateSchemas,dict)] = WeaviateSchema.class_objs) -> 'Weaviate':
        if not hasattr(cls, 'instance'):
            cls.instance = super(Weaviate, cls).__new__(cls)
            self = cls.instance
            self.host = host if host is not None else os.getenv('VECTOR_DB_HOST', '127.0.0.1')
            self.port = port if port is not None else os.getenv('VECTOR_DB_PORT', '8080')
            self.url = self.host + ":" + self.port
            
            self.create_schemas(schemas)
            self.add_references(schemas)
        return cls.instance    
    
    def create_schemas(self, schemas: list[(WeaviateSchemas,dict[str, any])]) -> None:
        for schema_entry in schemas:
            key, schema = schema_entry
            self.create_schema(key, schema)  
            self.schemas[key] = schema 
    
    def add_references(self, schemas: list[(WeaviateSchemas,dict[str, any])]) -> None:
        for schema_entry in schemas:
            key, schema = schema_entry
            for reference in schema.get('references', []):
                self.add_reference(key, reference)

    def create_schema(self, key: WeaviateSchemas, schema_object: dict[str, any]) -> None:
        try:
            vectorizer = wvc.config.Configure.Vectorizer.text2vec_transformers() if schema_object.get('vectorizer') else None
            props: list[Property] = schema_object['properties']
            properties: list[str] = [property.name for property in props]
            print("Creating new schema " + schema_object['class'] + " with vectorizer " + str(vectorizer), " properties ", properties)
            self.client.collections.create(schema_object['class'], 
                    properties = schema_object['properties'], 
                    vectorizer_config = vectorizer                               
            )                         
        except w.exceptions.UnexpectedStatusCodeError as e:
            print("Schema may already exist ")
            print("                  ", schema_object['class'], e)
        
    def add_reference(self, key: WeaviateSchemas, reference: dict[str, any]) -> None:
        print("Adding reference to ", key, " for " + reference.name)
        collection = self.collection(key)
        collection.config.add_reference(reference)

    def upsert(self, obj: dict[str, str], collection_key: WeaviateSchemas, id_property: str = None, attempts: int=0) -> bool:
        collection = self.collection(collection_key)   
        identifier = w.util.generate_uuid5(obj if id_property == None else obj.get(id_property, obj))
        
        try: 
            with collection.batch.rate_limit(requests_per_minute=5) as batch:
                batch.add_object(
                        obj,
                        uuid = identifier
                )
            failed_objs_a = collection.batch.failed_objects  # Get failed objects from the batch import
            failed_refs_a = collection.batch.failed_references
            print()
            print("failed_objs_a: ", failed_objs_a)
            print("failed_refs_a: ", failed_refs_a)
        except w.exceptions.WeaviateClosedClientError as e:
            self.reset_client()
            if attempts < 1:
                self.upsert(obj, collection_key, id_property, attempts+1)
            else:
                raise e
        return True
    
    def get_value_map(self, obj: dict[str, any], schema_object: dict[str, any], collection: str):
        props: list[Property] = schema_object[collection]
        reference_keys: list[str] = [property.name for property in props]
        return {key: obj.get(key) for key in reference_keys if obj.get(key) is not None}


    def truncate_collection(self, key: WeaviateSchemas) -> None:
        schema: dict[str, any] = WeaviateSchema.class_map[key]
        self.client.collections.delete(schema['class'])
        self.create_schema(key, schema)

    # private method
    def _upsert_sub_batches(self, collection: Collection[Properties, References], 
                            sbs: list[list[Document]], 
                            properties: dict[str, any], references: dict[str, any], attempts: int=0):
            count: int = 0
            for sub_batch in sbs:
                with collection.batch.dynamic() as batch:
                        for i, value in enumerate(sub_batch):
                            row = {"text": value.page_content, "ordinal": i}
                            row.update(properties)
                            identifier = weave_uuid5(row)
                            print("Upserting ", identifier, "with properties", properties)

                            batch.add_object(
                                properties=row,
                                references=references,
                                uuid=identifier
                            )
                        count += 1
            return count
 
    def upsert_text_vectorized(self, text: str, metaObj: dict[str, any], collection_key: WeaviateSchemas, attempts=0) -> bool:
        collection: Collection[Properties, References] = self.collection(collection_key)
        schema_object: dict[str, any] = WeaviateSchema.class_map[collection_key]
        references: dict[str, any] = self.get_value_map(metaObj, schema_object, 'references')
        properties: dict[str, any] = self.get_value_map(metaObj, schema_object, 'properties')
        split_text: list[Document] = utils.Utils.split(text)
        SUB_BATCH_SIZE: int = 50
        sub_batches: list[list[Document]] = [split_text[i:i + SUB_BATCH_SIZE] for i in range(0, len(split_text), SUB_BATCH_SIZE)]
        upserted_count: int = 0
        try:
            upserted_count = self._upsert_sub_batches(collection, sub_batches, properties, references)
        except w.exceptions.WeaviateClosedClientError as e:
            self.reset_client()
            if attempts < 1:
                self._upsert_sub_batches(collection, sub_batches[upserted_count:len(sub_batches)-1], properties, references, attempts+1)
            else:
                raise e
            
        return True
    
    def upsert_chunked_text(self, obj:dict[str, any], chunked_collection_key: WeaviateSchemas, metadata_collection_key: WeaviateSchemas, splitOn: str) -> bool:
        text = obj[splitOn]        
        del obj[splitOn]

        meta = self.upsert(obj=obj, collection_key=metadata_collection_key) 
        text = self.upsert_text_vectorized(text, obj, chunked_collection_key)     
        return meta and text
    
    def count(self, key: WeaviateSchemas) -> AggregateReturn:
        collection = self.collection(key)
        return collection.aggregate.over_all()
    
    def search(self, query:str, key: WeaviateSchemas, limit: int = 5, certainty: float = .7) -> list[dict[str, any]]:

        collection: Collection[Properties, References] = self.collection(key)

        response: list[dict[str, any]] = collection.query.near_text(
            query=query,
            limit=limit,
            certainty=certainty,
            return_metadata=wvc.query.MetadataQuery(distance=True)
        ).objects

        print("Found " + str(len(response)) + " objects")

        return response
    
    def get_by_ids(self, key: WeaviateSchemas, id_prop: str, ids: list[str]) -> list[dict[str, any]]:
        return self.collection(key).query.fetch_objects(
            filters= Filter.by_property(id_prop).contains_any(ids),
        ).objects
    
    def get_email_metadatas_in_thread(self, thread_id: str) -> list[EmailMessage]:
        results = self.collection(WeaviateSchemas.EMAIL).query.fetch_objects(
            filters=Filter.by_property("thread_id").equal(thread_id),
        )
        return [EmailMessage.model_validate(x.properties) for x in results.objects]

    def get_email_by_id(self, email_id: str) -> EmailMessage:
        results = self.collection(WeaviateSchemas.EMAIL).query.fetch_objects(
            filters=Filter.by_property("email_id").equal(email_id),
        )
        if len(results.objects)>0:
            text_results = self.collection(WeaviateSchemas.EMAIL_TEXT).query.fetch_objects(
                filters=Filter.by_property("email_id").equal(email_id),
                sort=Sort.by_property(name="ordinal", ascending=True),
            )
            print("Results", len(results.objects), " with text ", len(text_results.objects), "(",[x.uuid for x in text_results.objects],")")
            response = results.objects[0].properties
            response['text'] = [x.properties.get('text') for x in text_results.objects]
            self.email_update(response)
            return EmailMessage.model_validate(response)
        return None

    def email_update(self, props: dict[str, any]) -> None:
        utils.Utils.rename_key(props, 'from', 'sender')
        utils.Utils.rename_key(props, 'from_', 'sender')
            
    def get_emails(self) -> list[EmailMessage]:
        result = []
        for x in self.collection(WeaviateSchemas.EMAIL).iterator():
            x = x.properties
            self.email_update(x)
            result.append(EmailMessage.model_validate(x))
        return result
    
    def get_thread_by_id(self, thread_id: str) -> EmailThreadResponse:
        results = self.collection(WeaviateSchemas.EMAIL).query.fetch_objects(
            filters=Filter.by_property("thread_id").equal(thread_id),
        )
        if len(results.objects)>0:
            props = results.objects[0].properties
            self.email_update(props)
            return EmailThreadResponse.model_validate(props)
        return None

    def get_email_metadata_by_id(self, email_id: str) -> Email:
        results = self.collection(WeaviateSchemas.EMAIL).query.fetch_objects(
            filters=Filter.by_property("email_id").equal(email_id),
        ).objects
        if len(results)>0:
            props = results[0].properties
            self.email_update(props)

            return Email.model_validate(props)
        return None

    def get_thread_email_messages_by_id(self, thread_id: str) -> list[EmailTextWithFrom]:
        email_text_chunks = self.collection(WeaviateSchemas.EMAIL_TEXT).query.fetch_objects(
            filters=Filter.by_property("thread_id").equal(thread_id),
            sort=Sort.by_property(name="date", ascending = True),
        )
        email_text_by_ids: dict[str, dict[str, any]] = {}
        for email_text_chunk in email_text_chunks.objects:
            email_id = email_text_chunk.properties.get('email_id')
            email_text_by_ids[email_id] = email_text_chunk.properties
        email_metadata: list[Object[Properties, References]] = self.get_by_ids(WeaviateSchemas.EMAIL, "email_id", list(email_text_by_ids.keys()))
        for email_meta_entry in email_metadata:
            email_id = email_meta_entry.properties.get('email_id')
            text_entry = email_text_by_ids.get(email_id)
            kept = {}
            for k,v in text_entry.items():
                if v is not None:
                    kept[k] = v
            email_meta_entry.properties.update(kept)

        return Weaviate._collate_emails(email_metadata)
        
    @staticmethod
    def _collate_emails(email_metadata_date_sorted: list[Object[Properties, References]]) -> list[EmailTextWithFrom]:
        """Takes email text, which may have multiple parts, and collates them into a single email message for inclusion in a list of complete
        email messages in a thread. The email text is sorted by ordinal and then concatenated into a single text field. 
        IMPORTANT: Assumes email_metadata_date_sorted is sorted by date and thus that all email ids are consecutive entries."""
        output: list[EmailTextWithFrom] = []
        current_email_text_list: list[dict[str, any]] = []
        current_item: EmailTextWithFrom = None
        print("Collating emails", len(email_metadata_date_sorted))
        for obj in email_metadata_date_sorted:
            props: dict[str, any] = obj.properties
            email_id = props.get('email_id')
            print("Processing email ", email_id, current_item, current_email_text_list, obj.properties)
            if current_item is None:
                current_email_text_list = [{"text":props.get('text'), "ordinal":props.get('ordinal')}]
                current_item = EmailTextWithFrom(text = "", 
                    email_id=email_id, 
                    thread_id=props.get("thread_id"), 
                    ordinal=props.get("ordinal"), 
                    date=props.get("date"),
                    sender=props.get('sender'))   
            elif current_item.email_id != email_id:
                current_email_text_list = sorted(current_email_text_list, key=lambda x: x.get('ordinal'))
                current_item.text = "".join([x.get('text') for x in current_email_text_list])
                output.append(current_item)
                current_email_text_list = [{"text":props.get('text'), "ordinal":props.get('ordinal')}]
                current_item = EmailTextWithFrom(text = "", 
                    email_id=email_id, 
                    thread_id=props.get("thread_id"), 
                    ordinal=props.get("ordinal"), 
                    date=props.get("date"),
                    sender=props.get('sender'))   
            else:
                current_email_text_list.append({"text":props.get('text'), "ordinal":props.get('ordinal')})   
        if current_item is not None:
            current_email_text_list = sorted(current_email_text_list, key=lambda x: x.get('ordinal'))
            current_item.text = "".join([x.get('text') for x in current_email_text_list])
            output.append(current_item)                                              
        return output
    
    ### slack ###
    
    def get_slack_message_by_id(self, message_id: str) -> SlackMessage:
        results = self.collection(WeaviateSchemas.SLACK_MESSAGE).query.fetch_objects(
            filters=Filter.by_property("message_id").equal(message_id),
        )
        if len(results.objects)>0:
            text_results = self.collection(WeaviateSchemas.SLACK_MESSAGE_TEXT).query.fetch_objects(
                filters=Filter.by_property("message_id").equal(message_id),
                sort=Sort.by_property(name="ordinal", ascending=True),
            )
            print("Results", len(results.objects), " with text ", len(text_results.objects), "(",[x.uuid for x in text_results.objects],")")
            response = results.objects[0].properties
            utils.Utils.rename_key(response, 'from', 'sender')
            response['text'] = [x.properties.get('text') for x in text_results.objects]
            return SlackMessage.model_validate(response)
        return None
    
    def get_slack_messages(self) -> SlackResponse:
        result = [x.properties for x in self.collection(WeaviateSchemas.SLACK_MESSAGE).iterator()]
        for x in result:
            utils.Utils.rename_key(x, 'from', 'sender')
        return SlackResponse.model_validate({
            "messages": result
        })
    
    def get_slack_thread_by_id(self, thread_id: str) -> SlackThreadResponse:
        results = self.collection(WeaviateSchemas.SLACK_THREAD).query.fetch_objects(
            filters=Filter.by_property("thread_id").equal(thread_id),
        )
        if len(results.objects)>0:
            return SlackThreadResponse.model_validate(results.objects[0].properties)
        return None

    def get_slack_thread_messages_by_id(self, thread_id: str) -> SlackThreadResponse:
        results = self.collection(WeaviateSchemas.SLACK_THREAD).query.fetch_objects(
            filters=Filter.by_property("thread_id").equal(thread_id),
        )
        if len(results.objects)>0:
            thread = [x.properties for x in results.objects][0]
            message_results = self.collection(WeaviateSchemas.SLACK_MESSAGE).query.fetch_objects(
                filters=Filter.by_property("thread_id").equal(thread_id),
                sort=Sort.by_property(name="ts", ascending=True),
            )
            message_text_results = self.collection(WeaviateSchemas.SLACK_MESSAGE_TEXT).query.fetch_objects(
                filters=Filter.by_property("thread_id").equal(thread_id),
            )

            values = {}
            for text in message_text_results.objects:
                values[text.properties.get('message_id')] = text.properties.get('text')

            for message in message_results.objects:
                utils.Utils.rename_key(message.properties, 'from', 'sender')
                message.properties['text'] = [values.get(message.properties.get('message_id'))]
            
            thread['messages'] = [x.properties for x in message_results.objects]

            return SlackThreadResponse.model_validate(thread)
        return None
    
    ### documents
    
    def get_document_by_id(self, document_id: str) -> DocumentResponse:
        results = self.collection(WeaviateSchemas.DOCUMENT).query.fetch_objects(
            filters=Filter.by_property("document_id").equal(document_id),
        )
        if len(results.objects)>0:
            text_results = self.collection(WeaviateSchemas.DOCUMENT_TEXT).query.fetch_objects(
                filters=Filter.by_property("document_id").equal(document_id),
                sort=Sort.by_property(name="ordinal", ascending=True),
            )
            summary_results = self.collection(WeaviateSchemas.DOCUMENT_SUMMARY).query.fetch_objects(
                filters=Filter.by_property("document_id").equal(document_id),
            )

            print("Results", len(results.objects), " with text ", len(text_results.objects), "(",[x.uuid for x in text_results.objects],")")
            response = results.objects[0].properties
            response['text'] = [x.properties.get('text') for x in text_results.objects]
            response['summary'] = [x.properties.get('summary') for x in summary_results.objects][0] if len(summary_results.objects)>0 else {}
            return DocumentResponse.model_validate(response)
        return None
    
    def get_documents(self) -> list[DocumentResponse]:
        return [DocumentResponse.model_validate(x.properties) for x in self.collection(WeaviateSchemas.DOCUMENT).iterator()]

    #conferences

    def get_transcript_conversations(self) -> list[TranscriptConversation]:
        return [TranscriptConversation.from_weaviate_properties(x.properties) for x in self.collection(WeaviateSchemas.TRANSCRIPT).iterator()]

    def get_transcript_conversation_entries_for_id(self, meeting_code: str) -> list[TranscriptLine]:
        message_results = self.collection(WeaviateSchemas.TRANSCRIPT_ENTRY).query.fetch_objects(
                filters=Filter.by_property("meeting_code").equal(meeting_code),
                sort=Sort.by_property(name="ordinal", ascending=True),
                limit=1000
            )

        conversation: list[TranscriptLine] = []
        for x in message_results.objects:
            conversation.append(TranscriptLine(
                speaker=x.properties.get('speaker'),
                text=x.properties.get('text'),
                ordinal=x.properties.get('ordinal')
            ))

        conversation.sort(key=lambda x: x.ordinal)
        return conversation
    
    def get_transcript_conversation_by_meeting_code(self, meeting_code: str) -> TranscriptConversation:
        results = self.collection(WeaviateSchemas.TRANSCRIPT).query.fetch_objects(
            filters=Filter.by_property("meeting_code").equal(meeting_code),
        )
        if len(results.objects)>0:
            thread = [x.properties for x in results.objects][0]
            conversation = self.get_transcript_conversation_entries_for_id(meeting_code)
            return TranscriptConversation.from_weaviate_properties(thread, conversation)
            
        return None
    

    def close(self):       
        self.client.close()