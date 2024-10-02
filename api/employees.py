from hashlib import md5
from typing import Annotated, List, Optional

from fastapi.security import OAuth2PasswordBearer

from globals import Globals
from library.data.local.neo4j import Neo4j
from library.managers.auth_manager import AuthManager
from library.models.api_models import ApiResponse
from library.managers.api_support import APISupport

from library.models.employee import Employee, User
from library.managers.employee_manager import EmployeeManager
from fastapi import APIRouter, Body, Depends, UploadFile

from library.workday import Workday

route = APIRouter(tags=["Employees"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login/openapi")

@route.put('/employees')
async def add_employees_from_workday_export(me: Annotated[User, Depends(AuthManager.get_user_dependency(oauth2_scheme))],
                                            workday_csv_export: UploadFile) -> ApiResponse[str]:  
    """Add employees from a Workday export with columns 
    EmployeeID, Name, ManagerID, ManagerName, Location, Title, WorkEmail, Type, CostCenter, CostCenterHierarchy"""
    workday_csv_text: str = (await workday_csv_export.read()).decode("utf-8")
    print("Received Workday export")
    print(workday_csv_text)
    filename = Globals().resource(md5(workday_csv_text.encode()).hexdigest() + ".csv")
    with open(filename, "w") as f:
        f.write(workday_csv_text)
    employees: list[Employee] = Employee.from_csv_text(workday_csv_text)
    org = Workday(employees).org_chart()

    print("Org chart:")
    print(org)
    graph = Neo4j(protocol="bolt")
    graph.process_org_chart(org)
    return ApiResponse.create("True")

@route.get('/employees/reports/above')
async def employees_above(me: Annotated[User, Depends(AuthManager.get_user_dependency(oauth2_scheme))],
                          email: Optional[str] = None) -> ApiResponse[List[Employee]]:  
    """Retrieve the reporting chain above the specified user."""
    if not email:
        email = me.email
    emp_manager = EmployeeManager()
    chain = emp_manager.get_reporting_chain(email)

    for emp in chain:
        # this will be messy in the response
        emp.manager = None
    return ApiResponse.create(chain)

@route.get('/employees/reports/below')
async def employees_below(me: Annotated[User, Depends(AuthManager.get_user_dependency(oauth2_scheme))],
                          email:  Optional[str] = None) -> ApiResponse[Employee]:  
    """Retrieve user and the organization below them"""
    if not email:
        email = me.email
    emp_manager = EmployeeManager()
    report: Employee = emp_manager.get_reports(email)
    if report is None:
        APISupport.error_response(404, f"Employee with email {email} not found")
    remove_manager(report)
    return ApiResponse.create(report)

@route.get('/employees/me')
async def me(me: Annotated[User, Depends(AuthManager.get_user_dependency(oauth2_scheme))]) -> ApiResponse[Employee]:  
    """Retrieve current user"""
    return ApiResponse.create(me)

def remove_manager(emp: Employee) -> Employee:
    emp.manager = None
    for e in emp.reports:
        remove_manager(e)
    return emp