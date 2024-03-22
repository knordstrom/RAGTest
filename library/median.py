
from typing import List

class Solution:

    def __merge(self, nums1: List[int], nums2: List[int]) -> List[int]:
        """Merge two sorted arrays into one sorted array."""
        result = []
        if (len(nums1) == 0):
            result = nums2
        elif (len(nums2) == 0):
            result = nums1
        else:
            (left, right) = (nums1, nums2) if nums1[0] < nums2[0] else (nums2, nums1)
            i = 0 
            j = 0

            def areRightsBeforeNextLeft(i, j):
                return i < len(left) - 1 and j < len(right) and right[j] < left[i + 1]
            
            def areRightsAfterLastLeft(i, j):
                return i == len(left) - 1 and j < len(right)
            
            while i < len(left):
                result.append(left[i])
                while areRightsBeforeNextLeft(i, j) or areRightsAfterLastLeft(i, j):
                    result.append(right[j])
                    j += 1
                i += 1
        for k in range(0, 3, 1):
            print("")
        return result

    def __checkSorted(self, nums: List[int]) -> bool:
        """Check if the array is sorted."""
        for i in range(0, len(nums) - 1, 1):
            if nums[i] > nums[i + 1]:
                return False
        return True

    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:

        if nums1 is None:
            nums1 = []  
        if nums2 is None:   
            nums2 = []
        
        if not self.__checkSorted(nums1) or not self.__checkSorted(nums2):
            raise ValueError("The input arrays are not sorted")
        
        merged = self.__merge(nums1, nums2)

        if len(merged) == 0:
            return None
        elif len(merged) % 2 == 0:
            return (merged[len(merged) // 2 - 1] + merged[len(merged) // 2]) / 2
        else:
            return merged[len(merged) // 2]
    