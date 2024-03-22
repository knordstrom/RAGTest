# -*- coding: utf-8 -*-

import library.median as median
import unittest


class MedianTestSuite(unittest.TestCase):
    """Testing median solutions"""

    def test_none_none(self):
        s = median.Solution()
        assert s.findMedianSortedArrays([], []) == None 

    def test_13_2(self):
        s = median.Solution()
        assert s.findMedianSortedArrays([1, 3], [2]) == 2
        
    def test_none_25(self):
        s = median.Solution()
        assert s.findMedianSortedArrays(None, [2, 5]) == 3.5
        assert s.findMedianSortedArrays([], [2, 5]) == 3.5

    def test_134_none(self):
        s = median.Solution()
        assert s.findMedianSortedArrays([1, 3, 4], None) == 3
        assert s.findMedianSortedArrays([1, 3, 4], []) == 3

    def test_134_25(self):
        s = median.Solution()
        assert s.findMedianSortedArrays([1, 3, 4], [2, 5]) == 3
    
    def test_234_125(self):
        s = median.Solution()
        assert s.findMedianSortedArrays([2, 3, 4], [1, 2, 5]) == 2.5
        
if __name__ == '__main__':
    unittest.main()