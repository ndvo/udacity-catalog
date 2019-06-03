import flask
from flask import request, jsonify, Flask , make_response
from flask import session as login_session
from sqlalchemy import asc, desc
import random, string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests

app = Flask(__name__, template_folder="templates", static_url_path="")
app.secret_key = b'97wt2msdeaijknitaoc,.h pc/,teias'


import models
from models import session

class Page():
    title = ""
    content = ""
    model = ""
    login_session = login_session

    

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

def load_session_state():
    """ Creates a new session state. """
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state

CLIENT_ID = json.loads(open('client_secret_1018963645552-u7guasss4dhb2017u5n7v1o64ag6vl10.apps.googleusercontent.com.json', 'r').read())
@app.route('/gconnect', methods=['POST'])
def gconnect():
    if 'state' not in login_session.keys():
        load_session_state()
    if request.args.get('state') != login_session['state']:
        print request.args.get('state'), login_session['state']
        print request.args
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data
    print request.data, code
    try: 
        oauth_flow = flow_from_clientsecrets('client_secret_1018963645552-u7guasss4dhb2017u5n7v1o64ag6vl10.apps.googleusercontent.com.json',  scope ='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
        print "oi"
    except FlowExchangeError as e :
        response = make_response(json.dumps('Failed to upgrade authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        print e
        return response
    access_token = credentias.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's user ID doesn't match given User ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    if result['issued_to'] != CLIENT_ID:
        response = make_response( json.dumps("Token's client ID does not match"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = request.get(userinfo_url, params=params)
    data = answer.json()
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    print login_session['username']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id


    output = """
        <h1>Welcome {}</h1>
        <img src="{}">
    """.format(login_session['username'] , login_session['picture'])
    return output




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
        return "Category page";

@app.route("/cateory/<category>/delete", methods=['GET', 'POST',  'DELETE'])
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
        return flask.render_template
    if request.method == 'POST':
        if request.form['action']=='all':
            for item in category.load_items():
                session.delete(item)
        session.delete(category)
        session.commit()


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

@app.route("/logo.png")
def logo():
    """ Serve the logo file. """
    return flask.send_from_directory("", 'logo.png')


def createUser(login_session):
    newuser = User(name=login_session['username'], email=login_session['email'], avatar = login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

def getUserID(email):
    try: 
        user = session.query(User).filter_by(email = email).one()
        return user.id
    except:
        return None
        

clientID = '1018963645552-u7guasss4dhb2017u5n7v1o64ag6vl10.apps.googleusercontent.com'




if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0', port=5000)

