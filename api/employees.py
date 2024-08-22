from typing import List

from library.models.api_models import ApiResponse
from library.managers.api_support import APISupport

from library.models.employee import Employee
from library.managers.employee_manager import EmployeeManager
from fastapi import APIRouter

route = APIRouter(tags=["Employees"])

@route.get('/employees/reports/above')
async def employees_above(email: str) -> ApiResponse[List[Employee]]:  
    """Retrieve the reporting chain above the specified user."""
    emp_manager = EmployeeManager()
    chain = emp_manager.get_reporting_chain(email)

    for emp in chain:
        # this will be messy in the response
        emp.manager = None
    return ApiResponse.create(chain)

@route.get('/employees/reports/below')
async def employees_below(email: str) -> ApiResponse[Employee]:  
    """Retrieve user and the organization below them"""
    emp_manager = EmployeeManager()
    report: Employee = emp_manager.get_reports(email)
    if report is None:
        APISupport.error_response(404, f"Employee with email {email} not found")
    remove_manager(report)
    return ApiResponse.create(report)

def remove_manager(emp: Employee) -> Employee:
    emp.manager = None
    for e in emp.reports:
        remove_manager(e)
    return emp