import ast
from datetime import datetime
import os
import random
from typing import Optional
import uuid
import pytest
import requests
from library.data.local import weaviate as w
from library.models.api_models import EmailMessage
from library.models.employee import Employee
import library.managers.handlers as h
from requests.exceptions import ConnectionError

from library.managers.importance import ImportanceService
from library.models.message import Message
from library.models.weaviate_schemas import WeaviateSchemas
from tests.integration.library.integration_test_base import IntegrationTestBase

class TestImportanceService(IntegrationTestBase):
    
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

        weaviate_port = docker_services.port_for("weaviate", 8081)
        weaviate_url = "http://{}:{}".format(docker_ip, weaviate_port)
        docker_services.wait_until_responsive(
            timeout=60.0, pause=0.1, check=lambda: self.is_responsive(weaviate_url)
        )
        neo4j_port = docker_services.port_for("neo4j", 7574)
        neo4j_url = "http://{}:{}".format(docker_ip, neo4j_port)
        docker_services.wait_until_responsive(
            timeout=60.0, pause=0.1, check=lambda: self.is_responsive(neo4j_url)
        )
        return {
            'weaviate': {
                'url': weaviate_url,
                'host': docker_ip,
                'port': str(weaviate_port)
            },
            'neo4j': {
                'url': neo4j_url,
                'host': docker_ip,
                'port': str(neo4j_port)
            }
        }

    def test_importance_service_email_importance(self, service):
        lead: Employee = self.generate_employee("a@b.c", None)
        sb1_1: Employee = self.generate_employee("b@c.d", lead)
        sb1_2: Employee = self.generate_employee("c@d.e", lead)

        sb2_1: Employee = self.generate_employee("d@e.f", sb1_1)
        sb3_1: Employee = self.generate_employee("e@f.g", sb2_1)
        sb4_1: Employee = self.generate_employee("f@g.h", sb3_1)

        sb2_2: Employee = self.generate_employee("g@h.i", sb1_2)
        sb3_2: Employee = self.generate_employee("h@i.j", sb2_2)
        sb4_2: Employee = self.generate_employee("i@j.k", sb3_2)


        assert ImportanceService._identity_importance(lead, lead.work_email) == 0, "Self reference should have importance 0"
        assert ImportanceService._identity_importance(lead, sb1_1.work_email) == 100, "Direct reports should have importance 100"

        assert ImportanceService._identity_importance(sb4_2, sb4_1.work_email) == 0, "Different reporting chains should have importance 0"

        assert ImportanceService._identity_importance(sb4_2, sb3_2.work_email) == 100, "A direct messageee from manager should have importance 100"
        assert ImportanceService._identity_importance(sb4_2, sb2_2.work_email) == 50, "A message from two up should have importance 50"

    def generate_employee(self, email: str, manager: Optional[Employee]):
        e = Employee(
            employee_id=str(random.randint(1, 9999)),
            name=uuid.uuid4().hex,
            manager_id=None,
            manager_name=None,
            location="New York",
            title=uuid.uuid4().hex,
            type="Employee",
            cost_center="123",
            cost_center_hierarchy="123.456",
            email=email

        )
        if manager is not None:
            e.manager_id= manager.manager_id
            e.manager_name = manager.name
            manager.add_report(e)
        
        return e