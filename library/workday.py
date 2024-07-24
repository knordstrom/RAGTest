


from library.employee import Employee


class Workday:
    def __init__(self, employees: list[Employee]):
        self.unattached_employees: list[Employee] = employees

    def org_chart(self) -> list[Employee]:
        org_chart: dict[str, Employee] = {}
        while len(self.unattached_employees) > 0:
            remaining: list[Employee] = []
            for employee in self.unattached_employees:
                org_chart[employee.employee_id] = employee
                if employee.manager_id == employee.employee_id:
                    print("Employee", employee.employee_id, "is top level")
                elif employee.manager_id in org_chart:
                    print("Employee", employee.employee_id, "reports to", employee.manager_id)
                    manager: Employee = org_chart[employee.manager_id]
                    manager.add_report(employee)
                    print("     => Manager", employee.manager_id, "has", len(manager.reports), "reports")
                else:
                    remaining.append(employee)
            self.unattached_employees = remaining
            print()
            print("Remaining employees", len(self.unattached_employees))
        
        result = []
        for employee in org_chart.values():
            if employee.manager_id == employee.employee_id:
                print("Top level employee", employee.name)
                result.append(employee)
        return result

