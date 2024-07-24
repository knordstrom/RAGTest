
import warnings
from library.neo4j import Neo4j
from library.workday import Workday, Employee
import dotenv
import os
warnings.simplefilter("ignore", ResourceWarning)

def start():
    dotenv.load_dotenv()

    employees = Employee.from_csv(os.path.join(os.path.dirname(__file__), '../resources', 'employees.csv'))
    org = Workday(employees).org_chart()

    graph = Neo4j(protocol="bolt")
    graph.process_org_chart(org)

    

if __name__ == '__main__':
    start()