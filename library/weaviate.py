import copy
import enum
import weaviate as w
#import langchain_experimental.text_splitter as lang_splitter
import langchain_text_splitters as lang_splitter
from langchain_community.embeddings import GPT4AllEmbeddings
from library.vdb import VDB 
import weaviate.classes as wvc
from weaviate.classes.config import Property, DataType

class WeaviateSchemas(enum.Enum):

    EMAIL = 'email'
    EMAIL_TEXT = 'email_text'

class WeaviateSchema:

    class_objs: list[(str,dict)] = ([
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
            ],
            "references": [
                wvc.config.ReferenceProperty(name="email_id", target_collection="Email"),
                wvc.config.ReferenceProperty(name="date", target_collection="Email"),
                wvc.config.ReferenceProperty(name="from", target_collection="Email"),
                wvc.config.ReferenceProperty(name="to", target_collection="Email"),
                wvc.config.ReferenceProperty(name="thread_id", target_collection="Email"),
            ],

            # Specify a vectorizer
            "vectorizer": True,
    })
])


class Weaviate(VDB):

    schemas = {}

    @property
    def client(self):
        return w.connect_to_local(
            port=8080,
        )

    def collection(self, key: WeaviateSchemas) -> object:
        schema = self.schemas[key]
        return self.client.collections.get(schema['class'])
    
    def __init__(self, url, schemas: list[(str,dict)] = WeaviateSchema.class_objs) -> None:
        self.url = url
        for schema_entry in schemas:
            key, schema = schema_entry
            self.create_schema(schema)  
            self.schemas[key] = schema 

    def create_schema(self, schema_object) -> None:
        try:
            vectorizer = wvc.config.Configure.Vectorizer.text2vec_transformers() if schema_object['vectorizer'] else None
            print("Creating new schema " + schema_object['class'] + " with vectorizer " + str(vectorizer))
            self.client.collections.create(schema_object['class'], 
                                        properties = schema_object['properties'], 
                                        references = schema_object.get('references', None),
                                        vectorizer_config = vectorizer                               
                                )                         
        except w.exceptions.UnexpectedStatusCodeError:
            print("Schema already exists")

    def upsertChunkedText(self, obj, key: WeaviateSchemas, metadataKey: WeaviateSchemas, splitOn: str) -> bool:
        text = obj[splitOn]
        split_text = self.split(text)
        collection = self.collection(key)
        metaCollection = self.collection(metadataKey)
        with metaCollection.batch.dynamic() as batch:
            batch.add_object(
                    obj,
                    uuid = w.util.generate_uuid5(obj)
            )

        with collection.batch.dynamic() as batch:
            for value in split_text:
                row = {
                        "text": value.page_content,
                    }
                batch.add_object(
                    row,
                    uuid = w.util.generate_uuid5(row)
            )
        return True
    
    def count(self, key: WeaviateSchemas) -> object:
        collection = self.collection(key)
        return collection.aggregate.over_all()

    def split(self, text:str) -> list:
        text_splitter = lang_splitter.CharacterTextSplitter(
            separator="\n\n",
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False,
        )
        # text_splitter = lang_splitter.SemanticChunker(GPT4AllEmbeddings())
        return text_splitter.create_documents([text])
    
    def search(self, query:str, key: WeaviateSchemas, limit: int = 5) -> list:

        collection = self.collection(key)

        response = collection.query.near_text(
            query=query,
            limit=limit,
            return_metadata=wvc.query.MetadataQuery(distance=True)
        )

        print("Found " + str(len(response.objects)) + " objects")

        return response
    
    def close(self):       
        self.client.close()
