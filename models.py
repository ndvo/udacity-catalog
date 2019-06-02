import flask
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()
engine = create_engine('sqlite:///base.db?check_same_thread=False')

DBsession = sessionmaker()
DBsession.bind = engine
DBsession.configure(bind=engine)
session = DBsession()

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key = True)
    name = Column(String(255))
    description = Column(Text())

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


class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key = True)
    name = Column(String(255))
    description = Column(Text())
    category_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship(Category)

    def to_link(self):
        self.href = '/category/'+str(self.category_id)+'/term/'+str(self.id)
        self.text = self.name
        self.title = 'Visit '+self.name+' page'
        self.htmlclass = 'item'


Base.metadata.create_all(engine)
