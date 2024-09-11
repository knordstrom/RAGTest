import csv
from typing import Optional, Union

from pydantic import BaseModel, Field

from library.models.person import Person
class Employee(BaseModel):

    employee_id:str
    name:str
    manager_id: Optional[str] = None
    manager_name: Optional[str] = None
    location:str
    title:str
    work_email:str = Field(alias='email', alias_priority = 0, validation_alias = 'email', serialization_alias = 'email')
    type_: str = Field(alias='type', alias_priority = 0, validation_alias = 'type', serialization_alias = 'type')
    cost_center:str
    cost_center_hierarchy:str
    reports: set['Employee'] = set()
    manager: Optional['Employee'] = None

    _report_map: dict[str, 'Employee'] = None
    @property
    def report_map(self): 
        if self._report_map is None:
            self._report_map = {r.work_email: r for r in self.reports}
        return self._report_map

    def __hash__(self) -> int:
        return self.work_email.__hash__()
    
    def __str__(self):
        return self.name + " (" + self.title + ") [" + self.employee_id + "]"
    
    def add_report(self, report: 'Employee'):
        report.manager = self
        self.reports.add(report)

    def path_above_to(self, other: Union['Employee', str]) -> list['Employee']:
        """Return a list of employees up the org chart from this employee.
        If the employee_id is not found, returns an empty list.
        The order of the response is such that the employee repreented by other is first and the one being queried is last.
        """
        if (type(other) == str and self.employee_id == other) or self == other:
            return [self]
        if self.manager is not None:
            up = self.manager.path_above_to(other)
            if len(up) > 0:
                up.append(self)
                return up
        return []
    
    def path_below_to(self, other: Union['Employee', str], sp = "") -> list['Employee']:
        """Return a list of employees dowwn the org chart from this employee.
        If the employee_id is not found, returns an empty list.
        The order of the response is such that the employee repreented by other is first and the one being queried is last."""
        #print(sp, self.employee_id, other)
        if (type(other) == str and self.employee_id == other) or self == other:
            return [self]
        for report in self.reports:
            down = report.path_below_to(other, sp + "     ")
            #print(sp + "   down: ", down)
            if len(down) > 0:
                down.append(self)
                return down
        return []

    def to_dict(self):
        p = Person(name = self.name, email = self.work_email)
        result = p.to_dict()
        result.update({
            'employee_id': self.employee_id,
            'location': self.location,
            'title': self.title,
            'type': self.type_,
            'cost_center': self.cost_center,
            'cost_center_hierarchy': self.cost_center_hierarchy,
        })
        return result
    
    def distance_to_up(self, email: str) -> Optional[int]:
        """Return the distance from this employee to the employee with the given email address.
        If the email address is not found, returns -1.
        """
        if self.work_email == email:
            return 0
        if self.manager is not None:
            if self.manager.work_email == email:
                return 1
            d = self.manager.distance_to_up(email)
            if d is not None:
                return d + 1
        return None

    def distance_to_down(self, email: str) -> Optional[int]:
        """Return the distance from this employee to the employee with the given email address.
        If the email address is not found, returns -1.
        """
        if self.work_email == email:
            return 0
        for r in self.reports:
            if r.work_email == email:
                return -1
            d = r.distance_to_down(email)
            if d is not None:
                return d - 1
        return None

    def distance_to(self, email: str) -> Optional[int]:
        """Return the distance from this employee to the employee with the given email address.
        If the email address is not found, returns -1.
        """
        if self.work_email == email:
            return 0
        
        distance_up = self.distance_to_up(email)
        if distance_up is not None:
            return distance_up
        
        distance_down = self.distance_to_down(email)
        if distance_down is not None:
            return distance_down
        return None  
    
    @staticmethod
    def from_workday_row(d: dict):
        print("         from_workday_row", d)        
        return Employee(employee_id = d['EmployeeID'], 
                        name = d['Name'], 
                        manager_id = d['ManagerID'], 
                        manager_name = d['ManagerName'], 
                        location = d['Location'], 
                        title = d['Title'], 
                        email = d['WorkEmail'], 
                        type = d['Type'], 
                        cost_center = d['CostCenter'], 
                        cost_center_hierarchy = d['CostCenterHierarchy'])
    
    @staticmethod
    def from_csv(file_name: str) -> list['Employee']:
        with open(file_name, newline='') as csvfile:
            return Employee.from_csv_text(csvfile)
    
    @staticmethod
    def from_csv_text(text: str) -> list['Employee']:
        employees: list['Employee'] = []
        reader = csv.DictReader(text.splitlines())
        for row in reader:
            employees.append(Employee.from_workday_row(row))
        return employees