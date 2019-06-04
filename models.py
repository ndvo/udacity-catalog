""" 
Creates the models of the data used in the application.

There are three models: User, Category and Item. Both items and categories have
associated users and items also have associated categories.

"""
import flask
import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()
engine = create_engine('sqlite:///base.db?check_same_thread=False')

DBsession = sessionmaker()
DBsession.bind = engine
DBsession.configure(bind=engine)
session = DBsession()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(150), unique=True, nullable=False)
    name = Column(String(150), nullable=True)
    avatar = Column(String(200))
    active = Column(Boolean, default=False)
    tokens = Column(DateTime, default=datetime.datetime.utcnow())

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key = True)
    name = Column(String(255))
    description = Column(Text())
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship(User)


    def load_items(self):
        try:
            return self.items
        except AttributeError:
            self.items = session.query(Item).filter_by(category_id = self.id)
            return self.items

    def load_items_links(self):
        self.items_links = []
        for i in self.load_items():
            i.to_link()
            self.items_links.append(flask.render_template('link.html', link=i))

    def to_link(self):
        self.href = '/category/'+str(self.id)
        self.text = self.name
        self.title = 'Visit '+self.name+' page'
        self.htmlclass = 'category'

    def serialize(self):
        self.load_items()
        return {
                'type': 'category',
                'id': self.id,
                'name': self.name,
                'description': self.description,
                'items' : [i.serialize() for i in self.items]
                }


class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key = True)
    name = Column(String(255))
    description = Column(Text())
    category_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship(User)

    def to_link(self):
        self.href = '/category/'+str(self.category_id)+'/item/'+str(self.id)
        self.text = self.name
        self.title = 'Visit '+self.name+' page'
        self.htmlclass = 'item'

    def serialize(self):
        return {
                'type': 'item',
                'id': self.id,
                'name': self.name,
                'description': self.description,
                'category_id': self.category_id
                }


Base.metadata.create_all(engine)
