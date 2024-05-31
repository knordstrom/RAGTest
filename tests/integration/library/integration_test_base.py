import pytest
import requests

from library.weaviate_schemas import WeaviateSchema, WeaviateSchemas


class IntegrationTestBase:


    def retrieve_name_type_maps(self, db_property_list: list, code_property_list: list):
        saved_map = {prop.name: prop.data_type.value for prop in db_property_list}
        code_map = {prop.name: prop.dataType.value for prop in code_property_list}
        return saved_map, code_map

    
    def show_nested_properties_match(self, response, key: WeaviateSchemas):
        map = WeaviateSchema.class_map[key]     
        print("Testing properties for ", map['class']) 
        self.recursive_show_properties_match(response[map['class']].properties, map["properties"])
        

    def recursive_show_properties_match(self, db_property_list: list, code_property_list: list, level=0):
        saved_map, code_map = self.retrieve_name_type_maps(db_property_list, code_property_list)

        for key in saved_map:
            assert saved_map.get(key) == code_map.get(key), "Mismatch in data type on saved_map for " + key + ": " + str(saved_map.get(key)) + " vs " + str(code_map.get(key))  

        for key in code_map:
            assert saved_map.get(key) == code_map.get(key), "Mismatch in data type on code_map for " + key + ": " + str(saved_map.get(key)) + " vs " + str(code_map.get(key))

        print("     DB property list", db_property_list)
        saved_nested_map = {prop.name: prop.nested_properties for prop in db_property_list if prop.nested_properties is not None}       
        code_nested_map = {prop.name: prop.nestedProperties for prop in code_property_list if prop.nestedProperties is not None}
        
        assert saved_nested_map.keys() == code_nested_map.keys(), "Keys do not match at level " + str(level) + ": " + str(saved_nested_map.keys()) + " vs " + str(code_nested_map.keys())

        for key in saved_nested_map:
            print("Testing nested properties for ", key, " at level ", (level + 1))
            self.recursive_show_properties_match(saved_nested_map[key], code_nested_map[key], level + 1)