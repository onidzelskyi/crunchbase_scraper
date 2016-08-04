from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, ForeignKey, UniqueConstraint, ForeignKeyConstraint


engine = create_engine('sqlite:///crunchbase.db', echo=True)
Base = declarative_base()


class Company(Base):
    __tablename__ = 'companies'

    company_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    crunchbase_link = Column(String)
    site_link = Column(String)
    linkedin_link = Column(String)
    effective_date = Column(Date)
    UniqueConstraint('company_id', 'effective_date')

    
class TeamMember(Base):
    __tablename__ = 'team_members'

    member_id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.company_id'), nullable=False)
    full_name = Column(String)
    position = Column(String)
    crunchbase_link = Column(String)
    linkedin_link = Column(String)
    personal_details = Column(String)
    UniqueConstraint('company_id', 'member_id')
    ForeignKeyConstraint(['company_id', 'effective_date', 'member_id'], 
                         ['companies.company_id', 'companies.effective_date', 'fundings.funding_id'])



class Funding(Base):
    __tablename__ = 'fundings'

    funding_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.company_id'), nullable=False)
    funding_date = Column(Date)
    funding_round = Column(String)
    funding_amount = Column(String)
    UniqueConstraint('company_id', 'funding_id')
    ForeignKeyConstraint(['company_id', 'funding_id'],
                         ['companies.company_id', 'fundings.funding_id'])
