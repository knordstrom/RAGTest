import ast
import time
import json
import os
from neo4j import Record
import pytest
import requests
from library import models, neo4j, weaviate as w
from library.employee import Employee
import library.handlers as h
from weaviate.classes.query import Filter
from requests.exceptions import ConnectionError

from library.weaviate_schemas import WeaviateSchema, WeaviateSchemas
from library.workday import Workday
from tests.integration.library.integration_test_base import IntegrationTestBase

class WithValue:
    def __init__(self, value):
        self.value = value

class TestEmployeeNeo4j(IntegrationTestBase):
    
    def is_responsive(self, url):
        try:
            print("Checking if service is responsive at ", url, " ... ")
            response = requests.get(url)
            if response.status_code == 200:
                print("Service is responsive")
                return True
        except ConnectionError:
            return False

    @pytest.fixture(scope="session")
    def service(self, docker_ip, docker_services):
        # """Ensure that service is up and responsive."""

        port = docker_services.port_for("neo4j", 7575)
        url = "http://{}:{}".format(docker_ip, port)
        docker_services.wait_until_responsive(
            timeout=30.0, pause=0.1, check=lambda: self.is_responsive(url)
        )
        return {
            'url': url,
            'host': docker_ip,
            'port': "7688"
        }
    

    def test_employee_model_create_contains_proper_structure(self, service):
        employees = Employee.from_csv(os.path.join(os.path.dirname(__file__), '../../resources', 'employees.csv'))
        workday = Workday(employees)
        org_chart = workday.org_chart()

        graph = neo4j.Neo4j(service['host'], service['port'], "bolt", "neo4j", "password")
        graph.connect()

        graph.process_org_chart(org_chart)

        response = graph.query("MATCH (n:Person)-[r]->(b:Person) RETURN n, r, b")
        result: list[Record] = [r for r in response.records]

        people = {}
        sentences = []
        for saved in result:
            p = saved['n']
            r = saved['r']
            b = saved['b']
            if r.type != "REPORTS_TO" and r.type != "MANAGES":
                continue
            if p.labels == {'Person'}:
                people[p['email']] = p
                sentences.append(f"{p['name']} {r.type} {b['name']}")

        
        assert len(people) == 25
        ceo = people['jdoe@superbigmegacorp.com']
        assert ceo['name'] == 'John Doe'
        assert ceo['employee_id'] == '000001'
        assert ceo['title'] == 'Chief Executive Officer'
        assert ceo['location'] == 'New York City'
        assert ceo['cost_center'] == 'Office of the CEO'
        assert ceo['cost_center_hierarchy'] == 'Administration'

        assert len(sentences) == 48
        for s in sentences:
            print(s)

        assert "Zack Jones MANAGES John Doe" not in sentences

        assert "John Doe MANAGES Zack Jones" in sentences
        assert "John Doe MANAGES Charles Montgomery Burns" in sentences
        assert "John Doe MANAGES Valeria Dumont" in sentences
        assert "John Doe MANAGES Chris Fraser" in sentences
        assert "Zack Jones REPORTS_TO John Doe" in sentences
        assert "Charles Montgomery Burns REPORTS_TO John Doe" in sentences
        assert "Valeria Dumont REPORTS_TO John Doe" in sentences
        assert "Chris Fraser REPORTS_TO John Doe" in sentences

        assert "Cleo Gubbins REPORTS_TO Zack Jones" in sentences
        assert "Bobby Alexrod REPORTS_TO Zack Jones" in sentences
        assert "Zack Jones MANAGES Cleo Gubbins" in sentences
        assert "Zack Jones MANAGES Bobby Alexrod" in sentences

        assert "Homer Compson REPORTS_TO Charles Montgomery Burns" in sentences
        assert "Haruki Garcia REPORTS_TO Charles Montgomery Burns" in sentences
        assert "Charles Montgomery Burns MANAGES Homer Compson" in sentences
        assert "Charles Montgomery Burns MANAGES Haruki Garcia" in sentences

        assert "Gabriel Yamakaza REPORTS_TO Valeria Dumont" in sentences
        assert "Calista Krishnamurthy REPORTS_TO Valeria Dumont" in sentences
        assert "Valeria Dumont MANAGES Gabriel Yamakaza" in sentences
        assert "Valeria Dumont MANAGES Calista Krishnamurthy" in sentences

        assert "Maureen Montevideo REPORTS_TO Chris Fraser" in sentences
        assert "Jackson Berini REPORTS_TO Chris Fraser" in sentences
        assert "Chris Fraser MANAGES Maureen Montevideo" in sentences
        assert "Chris Fraser MANAGES Jackson Berini" in sentences

        assert "William Gatos REPORTS_TO Cleo Gubbins" in sentences
        assert "Tracey Gastelum REPORTS_TO Cleo Gubbins" in sentences
        assert "Cleo Gubbins MANAGES William Gatos" in sentences
        assert "Cleo Gubbins MANAGES Tracey Gastelum" in sentences

        assert "Yingshao Hong REPORTS_TO Bobby Alexrod" in sentences
        assert "Morgan Lydstrom REPORTS_TO Bobby Alexrod" in sentences
        assert "Bobby Alexrod MANAGES Yingshao Hong" in sentences
        assert "Bobby Alexrod MANAGES Morgan Lydstrom" in sentences

        assert "Jeremy Hoosegow REPORTS_TO William Gatos" in sentences
        assert "Shaula Elle REPORTS_TO William Gatos" in sentences
        assert "William Gatos MANAGES Jeremy Hoosegow" in sentences
        assert "William Gatos MANAGES Shaula Elle" in sentences

        assert "Margaret Rosen REPORTS_TO Tracey Gastelum" in sentences
        assert "Wilford Hopkins REPORTS_TO Tracey Gastelum" in sentences
        assert "Tracey Gastelum MANAGES Margaret Rosen" in sentences
        assert "Tracey Gastelum MANAGES Wilford Hopkins" in sentences

        assert "Arturo Li REPORTS_TO Yingshao Hong" in sentences
        assert "Amanda Higginbotham REPORTS_TO Yingshao Hong" in sentences
        assert "Yingshao Hong MANAGES Arturo Li" in sentences
        assert "Yingshao Hong MANAGES Amanda Higginbotham" in sentences

        assert "Bruce Waymo REPORTS_TO Morgan Lydstrom" in sentences
        assert "Danforth Hamptons REPORTS_TO Morgan Lydstrom" in sentences
        assert "Morgan Lydstrom MANAGES Bruce Waymo" in sentences
        assert "Morgan Lydstrom MANAGES Danforth Hamptons" in sentences

