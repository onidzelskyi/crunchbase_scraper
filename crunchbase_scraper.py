from sqlalchemy.orm import sessionmaker


from tables import Base, engine


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
Session.configure(bind=engine) 
session = Session()


def main():
    company = Company()

    session.add(company)
    session.commit()
    
        
if __name__ == '__main__':
    main()