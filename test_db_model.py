import unittest

from tables import Company, TeamMember, Funding


class TestDBModel(unittest.TestCase):
 
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
 
    def test_numbers_3_4(self):
        self.assertEqual(12, 12)
 
