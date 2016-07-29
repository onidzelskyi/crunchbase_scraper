import unittest

from sqlalchemy.orm import sessionmaker

from tables import (Company, TeamMember, Funding, Base, engine)


class TestDBModel(unittest.TestCase):
 
    def setUp(self):
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        Session.configure(bind=engine) 
        self.session = Session()
    
    def tearDown(self):
        self.session.close()
        #Base.metadata.drop_all(engine)
 
    def test_add_company(self):
        data = dict()
        company = Company(**data)
        
        self.session.add(company)
        
        result = self.session.query(Company).all()
        
        self.assertEqual(len(result), 1)
        
 
