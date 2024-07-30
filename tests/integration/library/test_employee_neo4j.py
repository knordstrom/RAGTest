import os
from neo4j import Record
import pytest
import requests
from library import neo4j
from library.employee import Employee
from requests.exceptions import ConnectionError
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
        service = {
            'url': url,
            'host': docker_ip,
            'port': "7688"
        }

        employees = Employee.from_csv(os.path.join(os.path.dirname(__file__), '../../resources', 'employees.csv'))
        workday = Workday(employees)
        org_chart = workday.org_chart()

        graph = neo4j.Neo4j(service['host'], service['port'], "bolt", "neo4j", "password")

        graph.process_org_chart(org_chart)

        return service
    

    def test_employee_model_create_contains_proper_structure(self, service):
        graph = neo4j.Neo4j(service['host'], service['port'], "bolt", "neo4j", "password")

        ceos: list[Employee] = graph.get_chief_executives()
        assert len(ceos) == 1
        assert ceos[0].work_email == 'jdoe@superbigmegacorp.com'

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

    def test_get_org_chart_above(self, service):
        graph = neo4j.Neo4j(service['host'], service['port'], "bolt", "neo4j", "password")

        chain: list[Employee] = graph.get_org_chart_above('ahigginbotham@superbigmegacorp.com')
        assert len(chain) == 5 # 20, 16, 7, 2, 1
        assert [e.employee_id for e in chain] == ['000020', '000016', '000007', '000002', '000001']
        assert chain[0].work_email == 'ahigginbotham@superbigmegacorp.com'
        assert chain[-1].work_email == 'jdoe@superbigmegacorp.com'
        assert chain[0].manager == chain[1]
        assert chain[1].manager == chain[2]
        assert chain[2].manager == chain[3]
        assert chain[3].manager == chain[4]

    def test_get_org_chart_below(self, service):
        graph = neo4j.Neo4j(service['host'], service['port'], "bolt", "neo4j", "password")

        employee: Employee = graph.get_org_chart_below('cgubbins@superbigmegacorp.com')
        assert employee.name == 'Cleo Gubbins'
        first_level = {}
        for e in employee.reports:
            first_level[e.employee_id] = e
        assert '000014' in first_level
        assert '000015' in first_level

        reports14 = {}
        for e in first_level['000014'].reports:
            reports14[e.employee_id] = e

        reports15 = {}
        for e in first_level['000015'].reports:
            reports15[e.employee_id] = e

        assert '000018' in reports14
        assert 'C00001' in reports14
        assert '000019' in reports15
        assert 'C00002' in reports15
