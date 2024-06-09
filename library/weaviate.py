import copy
import enum
import weaviate as w
#import langchain_experimental.text_splitter as lang_splitter
from langchain_community.embeddings import GPT4AllEmbeddings
from library.vdb import VDB 
from library import utils
import weaviate.classes as wvc
from weaviate.classes.config import Property, DataType
from library.weaviate_schemas import WeaviateSchemas, WeaviateSchema
from weaviate.classes.query import Filter

class Weaviate(VDB):

    schemas = {}
    postponded_references = {}

    _client = None
    @property
    def client(self):
        if self._client is None:
            print("Connecting to " + self.url)
            self._client = w.connect_to_local(
                host=self.host,
                port=self.port,
            )
        return self._client

    def reset_client(self):
        self._client = None
        
    
    def collection(self, key: WeaviateSchemas) -> object:
        schema = self.schemas[key]
        return self.client.collections.get(schema['class'])
    
    def __new__(cls, host = '127.0.0.1', port = '8080', schemas: list[(WeaviateSchemas,dict)] = WeaviateSchema.class_objs) -> None:
        if not hasattr(cls, 'instance'):
            cls.instance = super(Weaviate, cls).__new__(cls)
            self = cls.instance
            self.host = host
            self.port = port
            self.url = host + ":" + port
            
            self.create_schemas(schemas)
            self.add_references(schemas)
        return cls.instance    
    
    def create_schemas(self, schemas) -> None:
        for schema_entry in schemas:
            key, schema = schema_entry
            self.create_schema(key, schema)  
            self.schemas[key] = schema 
    
    def add_references(self, schemas) -> None:
        for schema_entry in schemas:
            key, schema = schema_entry
            for reference in schema.get('references', []):
                self.add_reference(key, reference)

    def create_schema(self, key, schema_object) -> None:
        try:
            vectorizer = wvc.config.Configure.Vectorizer.text2vec_transformers() if schema_object.get('vectorizer') else None
            properties = [property.name for property in schema_object['properties']]
            print("Creating new schema " + schema_object['class'] + " with vectorizer " + str(vectorizer), " properties ", properties)
            self.client.collections.create(schema_object['class'], 
                    properties = schema_object['properties'], 
                    vectorizer_config = vectorizer                               
            )                         
        except w.exceptions.UnexpectedStatusCodeError as e:
            print("Schema may already exist ")
            print("                  ", schema_object['class'], e)
        
    def add_reference(self, key, reference) -> None:
        print("Adding reference to ", key, " for " + reference.name)
        collection = self.collection(key)
        collection.config.add_reference(reference)

    def upsert(self, obj, collection_key: WeaviateSchemas, id_property: str = None, attempts=0) -> bool:
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
            print("failed_objs_a: ", failed_objs_a)
            print("failed_refs_a: ", failed_refs_a)
        except w.exceptions.WeaviateClosedClientError as e:
            self.reset_client()
            if attempts < 1:
                self.upsert(obj, collection_key, id_property, attempts+1)
            else:
                raise e
        return True
    
    def get_value_map(self, obj, schema_object, collection):
        reference_keys = [property.name for property in schema_object[collection]]
        return {key: obj.get(key) for key in reference_keys if obj.get(key) is not None}


    def truncate_collection(self, key: WeaviateSchemas) -> None:
        schema = WeaviateSchema.class_map[key]
        c = self.collection(key)
        c.data.delete_many(
            where = Filter.by_property(schema['properties'][0].name).like("*"),
        )

    # private method
    def _upsert_sub_batches(self, collection, sbs, properties, references, attempts=0):
            count = 0
            for sub_batch in sbs:
                with collection.batch.dynamic() as batch:
                        for i, value in enumerate(sub_batch):
                            row = {"text": value.page_content, "ordinal": i}
                            row.update(properties)
                            identifier = w.util.generate_uuid5(row)
                            print("Upserting ", identifier, "with properties", properties)

                            batch.add_object(
                                properties=row,
                                references=references,
                                uuid=identifier
                            )
                        count += 1
            return count
    
            
    
    def upsert_text_vectorized(self, text: str, metaObj: dict, collection_key: WeaviateSchemas, attempts=0) -> bool:
        collection = self.collection(collection_key)
        schema_object = WeaviateSchema.class_map[collection_key]
        references = self.get_value_map(metaObj, schema_object, 'references')
        properties = self.get_value_map(metaObj, schema_object, 'properties')
        split_text = utils.Utils.split(text)
        SUB_BATCH_SIZE = 50
        sub_batches = [split_text[i:i + SUB_BATCH_SIZE] for i in range(0, len(split_text), SUB_BATCH_SIZE)]
        upserted_count = 0
        try:
            upserted_count = self._upsert_sub_batches(collection, sub_batches, properties, references)
        except w.exceptions.WeaviateClosedClientError as e:
            self.reset_client()
            if attempts < 1:
                self._upsert_sub_batches(collection, sub_batches[upserted_count:len(sub_batches)-1], properties, references, attempts+1)
            else:
                raise e
            
        return True
    
    def upsert_chunked_text(self, obj:dict, chunked_collection_key: WeaviateSchemas, metadata_collection_key: WeaviateSchemas, splitOn: str) -> bool:
        text = obj[splitOn]        
        del obj[splitOn]
        meta = self.upsert(obj=obj, collection_key=metadata_collection_key) 
        text = self.upsert_text_vectorized(text, obj, chunked_collection_key)     
        return meta and text
    
    def count(self, key: WeaviateSchemas) -> object:
        collection = self.collection(key)
        return collection.aggregate.over_all()
    
    def search(self, query:str, key: WeaviateSchemas, limit: int = 5, certainty = .7) -> list:

        collection = self.collection(key)

        response = collection.query.near_text(
            query=query,
            limit=limit,
            certainty=certainty,
            return_metadata=wvc.query.MetadataQuery(distance=True)
        )

        print("Found " + str(len(response.objects)) + " objects")

        return response
    
    def close(self):       
        self.client.close()