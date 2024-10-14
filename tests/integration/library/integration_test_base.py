import dotenv
import pytest
import requests

from globals import Globals
from library.data.local.weaviate import Weaviate
from library.models.weaviate_schemas import WeaviateSchema, WeaviateSchemas
from weaviate.classes.query import Filter
from weaviate.collections.collection import Collection
from weaviate.collections.classes.internal import Object
from weaviate.collections.classes.types import Properties, References
class IntegrationTestBase:

    print("Loading .env file")
    dotenv.load_dotenv(dotenv_path=Globals().root_resource("tests/.env"))

    def get_truncation_property(self, schema: dict) -> str:
        property = schema['properties'][0].name
        if not "id" in property:
            print("Property", property," is not id, searching for id property")
            for prop in schema['properties']:
                print("Checking property ", prop.name)
                if "id" in prop.name:
                    property = prop.name
                    breakproperty = schema['properties'][0].name
        if not "id" in property:
            print("Property", property," is not id, searching for id property")
            for prop in schema['properties']:
                print("Checking property ", prop.name)
                if "id" in prop.name:
                    property = prop.name
                    break
        return property
    
    def truncate_collection_and_return(self, weave: Weaviate, key: WeaviateSchemas) -> Collection[Properties, References]:
        """Truncates the values in a weaviate collection and returns it for use"""
        schema = WeaviateSchema.class_map[key]
        c = weave.collection(key)
        assert c is not None

        property = self.get_truncation_property(schema)
        print("Truncating collection ", schema['class'], " on property ", property)
        c.data.delete_many(
            where = Filter.by_property(property).like("*"),
        )

        check = [x for x in weave.collection(key).iterator()]

        print("Check len was ", len(check))
        assert len(check) == 0, "Collection " + schema['class'] + " was not properly truncated"
        
        return c

    def retrieve_name_type_maps(self, db_property_list: list, code_property_list: list):
        """Retrieve maps of name -> type for a list of properties from the database and the codebase"""

        saved_map = {prop.name: prop.data_type.value for prop in db_property_list}
        code_map = {prop.name: prop.dataType.value for prop in code_property_list}
        return saved_map, code_map

    
    def show_nested_properties_match(self, response, key: WeaviateSchemas):
        """Show the properties of a weaviate collection are the same in code and in the database, 
            leveraging a recursive bidirectional comparison"""

        map = WeaviateSchema.class_map[key]     
        print("Testing properties for ", map['class']) 
        self.recursive_show_properties_match(key, response[map['class']].properties, map["properties"])
        

    def recursive_show_properties_match(self, schema: WeaviateSchemas, db_property_list: list, code_property_list: list, level=0):
        """Recursively compare the properties of a weaviate collection are the same in code and in the database"""

        saved_map, code_map = self.retrieve_name_type_maps(db_property_list, code_property_list)

        for key in saved_map:
            assert saved_map.get(key) == code_map.get(key), "Mismatch in data type on saved_map (" + str(schema) + ") for " + key + ": " + str(saved_map.get(key)) + " vs " + str(code_map.get(key))  

        for key in code_map:
            assert saved_map.get(key) == code_map.get(key), "Mismatch in data type on code_map (" + str(schema) + ") for " + key + ": " + str(saved_map.get(key)) + " vs " + str(code_map.get(key))

        print("     DB property list", db_property_list)
        saved_nested_map = {prop.name: prop.nested_properties for prop in db_property_list if prop.nested_properties is not None}       
        code_nested_map = {prop.name: prop.nestedProperties for prop in code_property_list if prop.nestedProperties is not None}
        
        assert saved_nested_map.keys() == code_nested_map.keys(), "Keys for " + str(schema) + " do not match at level " + str(level) + ": " + str(saved_nested_map.keys()) + " vs " + str(code_nested_map.keys())

        for key in saved_nested_map:
            print("Testing nested properties for ", key, " at level ", (level + 1))
            self.recursive_show_properties_match(schema, saved_nested_map[key], code_nested_map[key], level + 1)

class ReadyResponse:
    url: str
    host: str
    port: str

    def __init__(self, url: str, host: str, port: str):
        self.url = url
        self.host = host
        self.port = port

class MultiReadyResponse:
    weaviate: ReadyResponse
    neo4j: ReadyResponse

    def __init__(self, weaviate: ReadyResponse, neo4j: ReadyResponse):
        self.weaviate = weaviate
        self.neo4j = neo4j