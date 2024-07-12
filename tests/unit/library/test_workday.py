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

        def sorted_ids(reports):
            reports = list(map(lambda e: e.employee_id, reports))
            reports.sort()
            return reports
        
        def employee(id: str, lead = org_chart[0]):
            return list(filter(lambda e: e.employee_id == id, lead.reports))[0]

        assert sorted_ids(org_chart[0].reports) == ['000002', '000003', '000004', '000005']

        assert sorted_ids(employee("000002").reports) == ['000006', '000007']
        assert sorted_ids(employee("000003").reports) == ['000008', '000009']
        assert sorted_ids(employee("000004").reports) == ['000010', '000011']
        assert sorted_ids(employee("000005").reports) == ['000012', '000013']

        e6 = employee("000006", employee("000002"))
        assert sorted_ids(e6.reports) == ['000014', '000015']
        assert sorted_ids(employee("000014", e6).reports) == ['000018','C00001']

        