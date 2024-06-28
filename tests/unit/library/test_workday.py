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

        assert sorted_ids(org_chart[0].reports) == ['000002', '000003', '000004', '000005']
        assert sorted_ids(org_chart[0].reports[0].reports) == ['000006', '000007']
        assert sorted_ids(org_chart[0].reports[1].reports) == ['000008', '000009']
        assert sorted_ids(org_chart[0].reports[2].reports) == ['000010', '000011']
        assert sorted_ids(org_chart[0].reports[3].reports) == ['000012', '000013']

        e6 = list(filter(lambda e: e.employee_id == "000006", org_chart[0].reports[0].reports))[0]
        assert sorted_ids(e6.reports) == ['000014', '000015']

        e14 = list(filter(lambda e: e.employee_id == "000014", e6.reports))[0]
        assert sorted_ids(e14.reports) == ['000018','C00001']

        