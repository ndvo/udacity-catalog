import flask
from flask import request, jsonify, Flask
from sqlalchemy import asc, desc
app = Flask(__name__, template_folder="templates", static_url_path="")


import models
from models import session

class Page():
    title = ""
    content = ""
    model = ""

    

@app.route("/")
def homepage():
    """ Creates the main page with a list of categories and a list of recent items."""
    categories = session.query(models.Category).all()
    page = Page()
    page.title = "Welcome"
    page.description = "A categorization application, that stores items into categories."
    if not categories:
        page.content = Page()
        page.content.title = "Sorry, there is no category yet."
        page.content.main =  "<p>There are no categories created yet. You may create some using the \"New Category\" link.</p>"
    else:
        page.content = Page()
        page.content.title = "Welcome to the Category App"
        page.content.main = "<p>This application allows you to organize items into categories and retrieve them properly.</p><h2>Recent items</h2>"
        categories = session.query(models.Category).order_by(asc(models.Category.name)).all()
        for c in categories:
            c.to_link()
        page.content.aside = "<h2>Categories</h2>"
        page.content.aside += flask.render_template('list.html', List=[flask.render_template('link.html', link=c) for c in categories])
        items = list(session.query(models.Item).order_by(desc(models.Item.id)).limit(10))
        for i in items:
            i.to_link()
        page.content.main += flask.render_template('list.html', List=[flask.render_template('link.html', link=i) for i in items])
    return flask.render_template('base.html', page=page);


@app.route("/categories", methods=['GET'])
def categories():
    """ Creates a list of the available categories. """
    if request.method == 'GET':
        page = Page()
        page.title = "Categories page";
        page.description = "The full list of the categories available"
        categories = list(session.query(models.Category).all())
        for i in categories:
            i.to_link()
            i.link = flask.render_template('link.html', link=i)
        page.content = Page()
        page.content.title = "Categories"
        page.content.main = flask.render_template('definitionlist.html', htmlclass="categories", definitions=categories)
        page.content.aside = ""
        return flask.render_template('base.html', page=page)

@app.route("/categories/add", methods=['GET', 'POST'])
def category_form():
    """ Creates or process the form to create or edit categories"""
    if request.method == 'POST':
        new_category = models.Category(name = request.form['name'], description=request.form['description'])
        session.add(new_category)
        session.commit()
        page = Page()
        page.content = Page()
        page.title = page.content.title = 'Success'
        page.content.main = flask.render_template('success.html')
        return flask.render_template('base.html', page=page)
    else:
        page = Page()
        page.content = Page()
        page.title = "Create a new category"
        page.description = "This page allows the creation of new categories to the application"
        page.content.title = "New category"
        page.content.main = flask.render_template('form_category.html')
        return flask.render_template('base.html', page=page)

@app.route("/category/<category>", methods=['GET'])
def category(category=None):
    """ Creates the page for a single category. """
    if request.method == 'POST':
        pass
    if request.method == 'GET':
        page = Page()
        category = session.query(models.Category).get(category)
        category.load_items_links()
        page.title = category.name
        page.description = "Describes the category "+category.name
        page.content = Page()
        page.content.title = category.name
        page.content.main = flask.render_template('category_main.html', category=category)
        page.content.model = 'category'
        page.content.id = category.id
        return flask.render_template('base.html', page=page)
    if request.method == 'PUT':
        pass
    if request.method == 'DELETE':
        return "Category page";


@app.route("/categories/<category>/term/add", methods=['GET', 'POST'])
def term_form(category=None):
    """ Creates or process the form to create or edit terms"""
    if request.method == 'POST':
        new_item = models.Item(name = request.form['name'], description=request.form['description'], category_id=int(category))
        session.add(new_item)
        session.commit()
        page = Page()
        page.content = Page()
        page.title = page.content.title = 'Success'
        page.content.main = flask.render_template('success.html')
        return flask.render_template('base.html', page=page)
    else:
        category = session.query(models.Category).get(category)
        page = Page()
        page.content = Page()
        page.title = "Create a new category"
        page.description = "This page allows the creation of new categories to the application"
        page.content.title = "New term in the category "+category.name
        page.content.main = flask.render_template('form_term.html', category=category)
        return flask.render_template('base.html', page=page)


@app.route("/category/<category>/term/<term>", methods=['GET', 'PUT', 'DELETE'])
def term(category=None, term=None):
    """ Creates a page for a single term of a category. """
    if request.method == 'POST':
        pass
    if request.method == 'GET':
        page = Page()
        category = session.query(models.Category).get(category)
        category.to_link()
        category.link = flask.render_template('link.html', link=category)
        term = session.query(models.Item).get(term)
        page.title = category.name+": "+term.name
        page.description = "This page describes "+term.name+" from the category "+category.name
        page.content = Page()
        page.content.title = term.name
        page.content.main = flask.render_template('term.html', category=category, item=term)
        return flask.render_template('base.html', page=page)
    if request.method == 'PUT':
        pass
    if request.method == 'DELETE':
        return "Category page";

@app.route("/catalog.json", methods=['GET'])
def api_full_catalog():
    """ Returns the full catalog.
    
    This may become heavy on the database if the application is heavily used.
    In such case, the results should be paginated.
    """
    categories = session.query(models.Category).all()
    return jsonify([c.serialize() for c in categories])

@app.route("/catalog/category/<category>.json", methods=['GET'])
def api_category(category=None):
    """ Returns the JSON data for a specific category given by a category id.
    
    This may become heavy on the database if a single category has a lot of items.
    In such case, the results should be paginated.
    """
    if not category:
        return jsonify("")
    category = session.query(models.Category).get(category)
    return jsonify(category.serialize())

@app.route("/style.css")
def css():
    """ Serve the main CSS file. """
    return flask.send_from_directory("", 'style.css')

if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0', port=5000)
