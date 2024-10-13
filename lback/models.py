from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer,DateTime
from datetime import datetime

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True  

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def save(self, session):
        self.validate()
        session.add(self)
        session.commit()

    def delete(self, session):
        session.delete(self)
        session.commit()

    @classmethod
    def get_all(cls, session):
        return session.query(cls).all()

    @classmethod
    def get_by_id(cls, session, id):
        return session.query(cls).filter_by(id=id).first()

    @classmethod
    def create(cls, session, **kwargs):
        instance = cls(**kwargs)
        instance.validate() 
        session.add(instance)
        session.commit()
        return instance

    def update(self, session, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.validate()  
        session.commit()

    def validate(self):
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id}>"
