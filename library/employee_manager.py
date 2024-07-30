from library.employee import Employee
from library.neo4j import Neo4j


class EmployeeManager:

    def __init__(self):
        self.datastore = Neo4j()

    def get_reporting_chain(self, email: str) -> list[Employee]:
        return self.datastore.get_org_chart_above(email)
    
    def get_reports(self, email: str) -> Employee:
        return self.datastore.get_org_chart_below(email)

    