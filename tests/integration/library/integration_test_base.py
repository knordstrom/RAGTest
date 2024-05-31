import pytest
import requests

from library.weaviate_schemas import WeaviateSchema, WeaviateSchemas


class IntegrationTestBase:

    def show_flat_properties_match(self, response, key: WeaviateSchemas):
        map = WeaviateSchema.class_map[key]
        saved_map = {prop.name: prop.to_dict().get('dataType') for prop in response[map['class']].properties}
        code_map = {prop.name: [prop.dataType.value] for prop in map["properties"]}

        for key in saved_map:
            assert saved_map.get(key) == code_map.get(key)

        for key in code_map:
            assert saved_map.get(key) == code_map.get(key)