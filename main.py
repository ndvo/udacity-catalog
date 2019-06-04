import flask
import httplib2
import json
import models
import random, string
import requests
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



class Page():
    """ Generic page class to store values to be passed to templates"""
    title = ""
    content = ""
    model = ""
    login_session = login_session

#TODO: update


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
        page.content.main = """
            <p>There are no categories created yet. You may create some using the \"New Category\" link.</p>
            """
    else:
        page.content = Page()
        page.content.title = "Welcome to the Category App"
        page.content.main = """
        <p>This application allows you to organize items into categories and retrieve them properly.</p>
        <h2>Recent items</h2>
        """
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
    return flask.render_template('base.html', page=page)

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
        print idinfo, 'idinfo'
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
    response = make_response(json.dumps({'user':login_session['username'], 'avatar':login_session['picture'], 'email':login_session['email']}), 200)
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
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
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
        page = Page()
        page.title = "Categories page"
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
        new_category = models.Category(name = request.form['name'], description=request.form['description'], user_id=login_session['user_id'])
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
        return "Category page"

@app.route("/category/<category>/delete", methods=['GET', 'POST',  'DELETE'])
def category_delete(category=None):
    """ Delete a category.
    
    If the value of action is all, every item associated to the category will also be deleted.
    """
    category = session.query(models.Category).get(category)
    if request.method == 'GET':
        page = Page()
        page.title = "Delete category "+category.name
        page.description = "Deletion page for category "+category.name
        page.content = Page()
        page.content.title = "Deleting category "+category.name
        page.content.main = flask.render_template('category_delete.html', category=category )
        return flask.render_template('base.html', page=page)
    if request.method == 'POST':
        print category
        deleted = []
        if request.form['action']=='all':
            for item in category.load_items():
                deleted.append(item.name)
                session.delete(item)
        session.delete(category)
        session.commit()
        page = Page()
        page.content = Page()
        page.title = page.content.title = "Category "+category.name+" was deleted"
        page.content.main = "The category was completely removed, including the following terms: "+", ".join([item.name for item in deleted])+"."
        return flask.render_template('base.html', page=page)

@app.route("/category/<category>/term/<term>/delete", methods=['GET', 'POST',  'DELETE'])
def term_delete(category=None, term=None):
    """ Delete a term.  """
    category = session.query(models.Category).get(category)
    term = session.query(models.Item).get(term)
    if request.method == 'GET':
        page = Page()
        page.title = "Delete term "+term.name+" from "+category.name
        page.description = "Deletion page for term "+term.name
        page.content = Page()
        page.content.title = "Deleting term "+term.name+" from "+category.name
        page.content.main = flask.render_template('term_delete.html', category=category , item=term)
        return flask.render_template('base.html', page=page)
    if request.method == 'POST':
        session.delete(term)
        session.commit()
        page = Page()
        page.content = Page()
        page.title = page.content.title = "Term "+term.name+" was deleted"
        page.content.main = "The term was completely removed."
        return flask.render_template('base.html', page=page)



@app.route("/categories/<category>/term/add", methods=['GET', 'POST'])
def term_form(category=None):
    """ Creates or process the form to create or edit terms"""
    if request.method == 'POST':
        new_item = models.Item(name = request.form['name'], description=request.form['description'], user_id=login_session['user_id'], category_id=int(category))
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
        page.content.id = term.id
        page.content.model = 'item'
        page.content.main = flask.render_template('term.html', category=category, item=term)
        return flask.render_template('base.html', page=page, category=category, item=term)
    if request.method == 'PUT':
        pass
    if request.method == 'DELETE':
        return "Category page"

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
    new_user = models.User(name=login_session['username'], email=login_session['email'], avatar = login_session['picture'])
    session.add(new_user)
    session.commit()
    user = session.query(models.User).filter_by(email=login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user = session.query(models.User).filter_by(id=user_id).one()
    return user

def getUserID(email):
    try: 
        user = session.query(models.User).filter_by(email = email).one()
        return user.id
    except:
        return None
        

clientID = '1018963645552-u7guasss4dhb2017u5n7v1o64ag6vl10.apps.googleusercontent.com'




if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0', port=5000)

