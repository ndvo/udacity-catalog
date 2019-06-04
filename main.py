"""

Main script that controls the application.

It implements routes and build responses based on provided templates.

"""
import flask
import httplib2
import json
import models
import random
import requests
import string
from flask import request, jsonify, Flask, make_response
from flask import session as login_session
from google.auth.transport import requests as grequests
from google.oauth2 import id_token
from models import session
from oauth2client.client import FlowExchangeError
from oauth2client.client import flow_from_clientsecrets
from sqlalchemy import asc, desc

app = Flask(__name__, template_folder="templates", static_url_path="")
app.secret_key = b'97wt2msdeaijknitaoc,.h pc/,teias'



class Page(object):
    """ Generic page class to store values to be passed to templates"""

    login_session = login_session

    def __init__(self, title="", contentmain="", model="", description="", root=True):
        self.title = ""
        self.aside = ""
        self.model = ""
        self.description = ""
        self.user = login_session['username'] if 'username' in login_session else None
        print self.user
        if root:
            self.content = Page(title=title, root=False)
            self.content.main = contentmain

    def set_content(self, title, main):
        """ Sets the value for content Page """
        try:
            self.content.title
        except AttributeError:
            self.content = Page(title=self.title, root=False)
            self.content.main = main

    def render(self):
        """ Creates a HTML string with the content of the page."""
        return flask.render_template('base.html', page=self)


@app.route("/")
def homepage():
    """ Creates the front page with a list of categories and a list of recent items."""

    categories = session.query(models.Category).all()
    page = Page(
        title="Wellcome",
        description="A categorization application, that stores items into categories.",
        )
    if not categories:
        page.set_content(
            title="Sorry, there is no category yet.",
            main="""
            <p>There are no categories created yet. You may create some using the \"New Category\" link.</p>
            """
            )
    else:
        page.set_content(
            title="Welcome to the Category App",
            main="""
            <p>This application allows you to organize items into categories and retrieve them properly.</p>
            <h2>Recent items</h2>
            """
            )
        categories = session.query(models.Category).order_by(asc(models.Category.name)).all()
        for c in categories:
            c.to_link()
        page.content.aside = "<h2>Categories</h2>"
        page.content.aside += flask.render_template(
            'list.html',
            List=[flask.render_template('link.html', link=c) for c in categories]
            )
        items = list(session.query(models.Item).order_by(desc(models.Item.id)).limit(10))
        for i in items:
            i.to_link()
        page.content.main += flask.render_template(
            'list.html',
            List=[flask.render_template('link.html', link=i) for i in items]
            )
    return page.render()

def load_session_state():
    """ Creates a new session state. """
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state

CLIENT_ID = "1018963645552-u7guasss4dhb2017u5n7v1o64ag6vl10.apps.googleusercontent.com"
@app.route('/gconnect', methods=['POST'])
def gconnect():
    if 'state' not in login_session.keys():
        load_session_state()
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    payload = json.loads(request.data)
    token = payload['id_token']
    try:
        idinfo = id_token.verify_oauth2_token(token, grequests.Request(), CLIENT_ID)
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer')
        userid = idinfo['sub']
    except ValueError as e:
        response = make_response(json.dumps('Invalid token'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    login_session['access_token'] = token
    login_session['username'] = idinfo['name']
    login_session['picture'] = idinfo['picture']
    login_session['email'] = idinfo['email']
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    response = make_response(
        json.dumps(
            {
                'user': login_session['username'],
                'avatar': login_session['picture'],
                'email':login_session['email']
                }
            ),
        200)
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route('/gdisconnect', methods=['POST'])
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    result = httplib2.Http().request(url, 'GET')[0]
    # Logout even if it is not possible to revoke token
    del login_session['access_token']
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
    return response



@app.route("/categories", methods=['GET'])
def categories():
    """ Creates a list of the available categories. """
    if request.method == 'GET':
        page = Page(
            title="Categories page",
            description="The full list of the categories available"
            )
        categories = list(session.query(models.Category).all())
        for i in categories:
            i.to_link()
            i.link = flask.render_template('link.html', link=i)
        page.content.title = "Categories"
        page.content.main = flask.render_template(
            'definitionlist.html',
            htmlclass="categories",
            definitions=categories
            )
        page.content.aside = ""
        return page.render()

@app.route("/categories/add", methods=['GET', 'POST'])
def category_form():
    if 'username' not in login_session:
        return Page(title="Unauthorized", contentmain="You are not authorized to see this page.").render()
    """ Creates or process the form to create"""
    if request.method == 'POST':
        new_category = models.Category(
            name=request.form['name'],
            description=request.form['description'],
            user_id=login_session['user_id']
            )
        session.add(new_category)
        session.commit()
        return Page(title='Success', contentmain=flask.render_template('success.html')).render()
    else:
        return Page(
            description="This page allows the creation of new categories to the application",
            title="Create a new category",
            contentmain=flask.render_template('form_category.html')
        ).render()


@app.route("/category/<category>", methods=['GET'])
def category(category=None):
    """ Creates the page for a single category. """
    if request.method == 'POST':
        pass
    if request.method == 'GET':
        category = session.query(models.Category).get(category)
        category.load_items_links()
        page = Page(
            title=category.name,
            description="Describes the category "+category.name
        )
        page.content.title = category.name
        page.content.main = flask.render_template('category_main.html', category=category)
        page.content.model = 'category'
        page.content.id = category.id
        return flask.render_template('base.html', page=page)
    if request.method == 'PUT':
        pass
    if request.method == 'DELETE':
        return "Category page"

@app.route("/category/<category>/edit", methods=['GET', 'POST'])
def category_edit(category=None):
    if 'username' not in login_session:
        return Page(title="Unauthorized", contentmain="You are not authorized to see this page.").render()
    if request.method == 'GET':
        category = session.query(models.Category).get(category)
        return Page(
            description="This page allows the creation of new categories to the application",
            title="Create a new category",
            contentmain=flask.render_template('form_category.html', category=category)
        ).render()
    if request.method == 'POST':
        category = session.query(models.Category).get(category)
        category.name = request.form['name']
        category.description = request.form['description']
        session.commit()
        return Page(title='Success', contentmain=flask.render_template('success.html')).render()


@app.route("/category/<category>/delete", methods=['GET', 'POST', 'DELETE'])
def category_delete(category=None):
    if 'username' not in login_session:
        return Page(title="Unauthorized", contentmain="You are not authorized to see this page.").render()
    """ Delete a category.

    If the value of action is all, every item associated to the category will also be deleted.
    """
    category = session.query(models.Category).get(category)
    if request.method == 'GET':
        return Page(
            title="Delete category "+category.name,
            description="Deletion page for category "+category.name,
            contentmain=flask.render_template('category_delete.html', category=category)
            ).render()
    if request.method == 'POST':
        deleted = []
        if request.form['action'] == 'all':
            for item in category.load_items():
                deleted.append(item.name)
                session.delete(item)
        session.delete(category)
        session.commit()
        return Page(
            title="Category "+category.name+" was deleted",
            contentmain="The category was completely removed, including the following terms: "+\
            ", ".join([item for item in deleted])+".").render()

@app.route("/category/<category>/term/<term>/delete", methods=['GET', 'POST', 'DELETE'])
def term_delete(category=None, term=None):
    if 'username' not in login_session:
        return Page(title="Unauthorized", contentmain="You are not authorized to see this page.").render()
    """ Delete a term.  """
    category = session.query(models.Category).get(category)
    term = session.query(models.Item).get(term)
    if request.method == 'GET':
        page = Page(
            title="Delete term "+term.name+" from "+category.name,
            description="Deletion page for term "+term.name
            )
        page.content.title = "Deleting term "+term.name+" from "+category.name
        page.content.main = flask.render_template('term_delete.html', category=category, item=term)
        return flask.render_template('base.html', page=page)
    if request.method == 'POST':
        session.delete(term)
        session.commit()
        page = Page()
        page.content = Page()
        page.title = page.content.title = "Term "+term.name+" was deleted"
        page.content.main = "The term was completely removed."
        return flask.render_template('base.html', page=page)



@app.route("/category/<category>/add/term", methods=['GET', 'POST'])
def term_form(category=None):
    if 'username' not in login_session:
        return Page(title="Unauthorized", contentmain="You are not authorized to see this page.").render()
    """ Creates or process the form to create"""
    if request.method == 'POST':
        new_item = models.Item(
            name=request.form['name'],
            description=request.form['description'],
            user_id=login_session['user_id'],
            category_id=int(category)
            )
        session.add(new_item)
        session.commit()
        return Page(title='Success', contentmain=flask.render_template('success.html')).render()
    else:
        category = session.query(models.Category).get(category)
        page = Page(
            title="Create a new category",
            description="This page allows the creation of new categories to the application",
            contentmain=flask.render_template('form_term.html', category=category)
            )
        return flask.render_template('base.html', page=page)


@app.route("/category/<category>/term/<term>", methods=['GET', 'PUT', 'DELETE'])
def term(category=None, term=None):
    """ Creates a page for a single term of a category. """
    if request.method == 'POST':
        pass
    if request.method == 'GET':
        category = session.query(models.Category).get(category)
        category.to_link()
        category.link = flask.render_template('link.html', link=category)
        term = session.query(models.Item).get(term)
        page = Page(
            title=category.name+": "+term.name,
            description="This page describes "+term.name+" from the category "+category.name,
            contentmain=flask.render_template('term.html', category=category, item=term)
            )
        page.content.id = term.id
        page.content.title = term.name
        page.content.model = 'item'
        return flask.render_template('base.html', page=page, category=category, item=term)
    if request.method == 'PUT':
        pass
    if request.method == 'DELETE':
        return "Category page"

@app.route("/category/<category>/term/<term>/edit", methods=['GET','POST'])
def term_edit(category=None, term=None):
    if 'username' not in login_session:
        return Page(title="Unauthorized", contentmain="You are not authorized to see this page.").render()
    category = session.query(models.Category).get(category)
    term = session.query(models.Item).get(term)
    if request.method == 'GET':
        page = Page(
            title="Edit the term "+term.name,
            description="This page allows the creation of new categories to the application",
            contentmain=flask.render_template(
                'form_term.html',
                category=category,
                item=term)
            )
        return flask.render_template('base.html', page=page)

    if request.method == 'POST':
        term.name = request.form['name']
        term.description = request.form['description']
        session.commit()
        return Page(title='Success', contentmain=flask.render_template('success.html')).render()
        

# JSON endpoints

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

@app.route("/logo.png")
def logo():
    """ Serve the logo file. """
    return flask.send_from_directory("", 'logo.png')


def createUser(login_session):
    new_user = models.User(
        name=login_session['username'],
        email=login_session['email'],
        avatar=login_session['picture']
        )
    session.add(new_user)
    session.commit()
    user = session.query(models.User).filter_by(email=login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user = session.query(models.User).filter_by(id=user_id).one()
    return user

def getUserID(email):
    try:
        user = session.query(models.User).filter_by(email=email).one()
        return user.id
    except:
        return None


clientID = '1018963645552-u7guasss4dhb2017u5n7v1o64ag6vl10.apps.googleusercontent.com'




if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
