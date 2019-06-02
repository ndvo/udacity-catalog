import flask
from flask import Flask
from flask import request
app = Flask(__name__, template_folder="templates")


import models
from models import session

class Page(): pass


@app.route("/")
def hello():
    categories = session.query(models.Category).all()
    return "Home page";

@app.route("/categories", methods=['GET', 'POST'])
def categories():
    if request.method == 'POST':
        pass
    if request.method == 'GET':
        page = Page()
        page.title = "Categories page";
        page.description = "The full list of the categories available"
        categories = session.query(models.Category).all()
        categories_names = [c.name for c in categories]
        page.content = Page()
        page.content.title = "Categories"
        page.content.main = flask.render_template('list.html', List=categories_names)
        page.content.aside = ""
        return flask.render_template('base.html', page=page)

@app.route("/categories/add", methods=['GET', 'POST'])
def caterogy_form():
    if request.method == 'POST':
        new_category = models.Category(name = request.form['name'], description=request.form['description'])
        session.add(new_category)
        session.commit()
        return """
        Success. Your data has been received.
        """
    else:
        return """
        <form method="POST" action="/categories/add" enctype="multipart/formdata">
        <label for="name">Name</label>
        <input type="text" name="name" placeholder="Choose a name for your category" />
        <textarea name="description"></textarea>
        <button type="submit">Submit</button>
        </form>
        """;

@app.route("/category/<category>", methods=['GET', 'PUT', 'DELETE'])
def category(category=None):
    if request.method == 'POST':
        pass
    if request.method == 'GET':
        return "Category page";
    if request.method == 'PUT':
        pass
    if request.method == 'DELETE':
        return "Category page";


@app.route("/category/<category>/terms", methods=['GET', 'POST'])
def terms(category=None):
    if request.method == 'GET':
        return "term page "+category;

@app.route("/category/<category>/term/<term>", methods=['GET', 'PUT', 'DELETE'])
def term(category=None):
    if request.method == 'POST':
        pass
    if request.method == 'GET':
        return "Category page";
    if request.method == 'PUT':
        pass
    if request.method == 'DELETE':
        return "Category page";








if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0', port=5000)
