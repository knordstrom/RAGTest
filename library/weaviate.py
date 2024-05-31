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
            vectorizer = wvc.config.Configure.Vectorizer.text2vec_transformers() if schema_object['vectorizer'] else None
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

    def upsert(self, obj, collection_key: WeaviateSchemas, id_property: str = None) -> bool:
        collection = self.collection(collection_key)   
        identifier = w.util.generate_uuid5(obj if id_property == None else obj.get(id_property, obj))
        with collection.batch.dynamic() as batch:
            batch.add_object(
                    obj,
                    uuid = identifier
            )
        return True
    
    def get_value_map(self, obj, schema_object, collection):
        reference_keys = [property.name for property in schema_object[collection]]
        return {key: obj[key] for key in reference_keys}
        
    
    def upsert_text_vectorized(self, text: str, metaObj: dict, collection_key: WeaviateSchemas) -> bool:
        collection = self.collection(collection_key)
        schema_object = WeaviateSchema.class_map[collection_key]
        references = self.get_value_map(metaObj, schema_object, 'references')
        properties = self.get_value_map(metaObj, schema_object, 'properties')
        split_text = utils.Utils.split(text)
        with collection.batch.dynamic() as batch:
            for value in split_text:
                row = {
                        "text": value.page_content,
                    }
                row.update(properties)
                batch.add_object(
                    properties = row,
                    references = references,
                    uuid = w.util.generate_uuid5(row)
            )
        return True

    def upsertChunkedText(self, obj:dict, chunked_collection_key: WeaviateSchemas, metadata_collection_key: WeaviateSchemas, splitOn: str) -> bool:
        text = obj[splitOn]        
        del obj[splitOn]
        meta = self.upsert(obj, metadata_collection_key) 
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