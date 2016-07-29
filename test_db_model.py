import unittest
import yaml

from sqlalchemy.orm import sessionmaker

from tables import (Company, TeamMember, Funding, Base, engine)


class TestDBModel(unittest.TestCase):
 
    def setUp(self):
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        Session.configure(bind=engine) 
        self.session = Session()

        with open('fixtures.yaml') as fin:
            self.fixtures = yaml.load(fin)
    
    def tearDown(self):
        self.session.close()
        #Base.metadata.drop_all(engine)
 
    def test_add_company(self):
        data = self.fixtures['companies'][0]
        company = Company(**data)
        
        self.session.add(company)
        
        result = self.session.query(Company).all()
        
        self.assertEqual(len(result), 1)
        
 
