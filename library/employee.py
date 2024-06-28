import csv

from library.person import Person
class Employee:

    def __init__(self, employee_id: str, name: str, manager_id: str, manager_name: str, location: str, title: str, work_email: str, 
                 type: str, cost_center: str, cost_center_hierarchy: str):
        self.employee_id = employee_id
        self.name = name
        self.manager_id = manager_id
        self.manager_name = manager_name
        self.location = location
        self.title = title
        self.work_email = work_email
        self.type = type
        self.cost_center = cost_center
        self.cost_center_hierarchy = cost_center_hierarchy
        self.reports = []

    def __str__(self):
        return self.name + " (" + self.title + ") [" + self.employee_id + "]"
    
    def add_report(self, report):
        self.reports.append(report)

    def to_dict(self):
        p = Person(self.name, self.work_email)
        result = p.to_dict()
        result.update({
            'employee_id': self.employee_id,
            'location': self.location,
            'title': self.title,
            'type': self.type,
            'cost_center': self.cost_center,
            'cost_center_hierarchy': self.cost_center_hierarchy,
        })
        return result
    
    @staticmethod
    def from_dict(d: dict):
        return Employee(d['EmployeeID'], d['Name'], d['ManagerID'], d['ManagerName'], d['Location'], d['Title'], d['WorkEmail'], 
                        d['Type'], d['CostCenter'], d['CostCenterHierarchy'])
    
    @staticmethod
    def from_csv(file_name: str):
        employees = []
        with open(file_name, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                employees.append(Employee.from_dict(row))
        return employees