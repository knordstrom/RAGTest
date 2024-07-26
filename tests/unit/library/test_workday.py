import random
import unittest
import unittest
import os
import library.workday as wd

class WorkdayTest(unittest.TestCase):

    def test_org_chart_gets_constructed_in_any_order(self):
        employees = wd.Employee.from_csv(os.path.join(os.path.dirname(__file__), '../../resources', 'employees.csv'))
        random.shuffle(employees)
        assert len(employees) == 25
        for e in employees:
            assert len(e.reports) == 0

        workday = wd.Workday(employees)
        org_chart = workday.org_chart()
        assert len(org_chart) == 1

        def employee_ids(reports: list[wd.Employee]) -> list[str]:
            v = list(map(lambda e: e.employee_id, reports))
            v.reverse()
            return v

        def sorted_ids(reports: list[wd.Employee]):
            reports = list(map(lambda e: e.employee_id, reports))
            reports.sort()
            return reports
        
        def employee(id: str, lead: wd.Employee = org_chart[0]):
            return list(filter(lambda e: e.employee_id == id, lead.reports))[0]
        
        lead = org_chart[0]

        assert sorted_ids(org_chart[0].reports) == ['000002', '000003', '000004', '000005']

        assert sorted_ids(employee("000002").reports) == ['000006', '000007']
        assert sorted_ids(employee("000003").reports) == ['000008', '000009']
        assert sorted_ids(employee("000004").reports) == ['000010', '000011']
        assert sorted_ids(employee("000005").reports) == ['000012', '000013']

        assert sorted_ids(employee("000002").reports) == ['000006', '000007']
        assert sorted_ids(employee("000003").reports) == ['000008', '000009']
        assert sorted_ids(employee("000004").reports) == ['000010', '000011']
        assert sorted_ids(employee("000005").reports) == ['000012', '000013']

        e6 = employee("000006", employee("000002"))
        e6 = employee("000006", employee("000002"))
        assert sorted_ids(e6.reports) == ['000014', '000015']
        assert sorted_ids(employee("000014", e6).reports) == ['000018','C00001']

        assert lead.manager == None
        assert len(lead.path_above_to(e6)) == 0
        assert e6.path_above_to(lead) == [lead, employee("000002"), e6]
        
        assert lead.path_below_to(e6) == [e6, employee("000002"), lead]
        assert len(lead.path_below_to("00018")) == 0 # no such employee
        assert len(lead.path_below_to("000018")) == 5

        assert employee_ids(lead.path_below_to("000018")) == ['000001', '000002', '000006', '000014', '000018']
        assert employee_ids(lead.path_below_to("C00001")) == ['000001', '000002', '000006', '000014', 'C00001']

        assert employee_ids(lead.path_below_to("000019")) == ['000001', '000002', '000006', '000015', '000019']
        assert employee_ids(lead.path_below_to("C00002")) == ['000001', '000002', '000006', '000015', 'C00002']

        assert employee_ids(lead.path_below_to("000020")) == ['000001', '000002', '000007', '000016', '000020']
        assert employee_ids(lead.path_below_to("C00003")) == ['000001', '000002', '000007', '000016', 'C00003']

        assert employee_ids(lead.path_below_to("000021")) == ['000001', '000002', '000007', '000017', '000021']
        assert employee_ids(lead.path_below_to("C00004")) == ['000001', '000002', '000007', '000017', 'C00004']





        
        ###
        # 000001
        #    |
        #    +-- 000002
        #    |     |
        #    |     +-- 000006
        #    |     |     |
        #    |     |     +-- 000014
        #    |     |     |     |
        #    |     |     |     +-- 000018
        #    |     |     |     |
        #    |     |     |     +-- C00001
        #    |     |     |
        #    |     |     +-- 000015
        #    |     |           |
        #    |     |           +-- 000019
        #    |     |           |   
        #    |     |           +-- C00002
        #    |     |
        #    |     +-- 000007
        #    |           |      
        #    |           +-- 000016
        #    |           |     |
        #    |           |     +-- 000020
        #    |           |     |   
        #    |           |     +-- C00003     
        #    |           |
        #    |           +-- 000017
        #    |                 |
        #    |                 +-- 000021
        #    |                 |
        #    |                 +-- C00004
        #    |
        #    +-- 000003
        #    |     |
        #    |     +-- 000008
        #    |     |
        #    |     +-- 000009
        #    |
        #    +-- 000004
        #    |     |
        #    |     +-- 000010
        #    |     |
        #    |     +-- 000011
        #    |
        #    +-- 000005
        #          |
        #          +-- 000012
        #          |
        #          +-- 000013
        ###
