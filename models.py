
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()
engine = create_engine('sqlite:///base.db')

DBsession = sessionmaker()
DBsession.bind = engine
DBsession.configure(bind=engine)
session = DBsession()

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key = True)
    name = Column(String(255))
    description = Column(Text())



class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key = True)
    name = Column(String(255))
    description = Column(Text())
    category_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship(Category)

Base.metadata.create_all(engine)
