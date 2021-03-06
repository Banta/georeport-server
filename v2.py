"""
    GeoReport v2 Server
    -------------------

    Open311 GeoReport v2 Server implementation written in Flask.

    :copyright: (c) Miami-Dade County 2011
    :author: Julian Bonilla (@julianbonilla)
    :license: Apache License v2.0, see LICENSE for more details.
"""
import os
from data import service_types, service_definitions, service_discovery, srs
from flask import Flask, g, render_template, request, abort, json, jsonify, make_response
import random
import flaskext.couchdb
from couchdbkit import *

# Configuration
DEBUG = True
ORGANIZATION = 'Code for America'
JURISDICTION = 'codeforamerica.org'
COUCHDB_SERVER = 'http://geopher.net:5984/'
COUCHDB_DATABASE = 'cfa311'

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('GEOREPORT_SETTINGS', silent=True)

manager = flaskext.couchdb.CouchDBManager()
manager.setup(app)
# manager.add_viewdef(docs_by_author)  # Install the view
# manager.sync(app)

#couchdb init
server = Server(uri='http://geopher.net:5984')
db = server.get_db('cfa311')

@app.route('/')

def index():
    return render_template('index.html', org=app.config['ORGANIZATION'], 
                           jurisdiction=app.config['JURISDICTION'])

@app.route('/create_request')
def create_request():
    return render_template('create_request.html')

@app.route('/discovery.<format>')
def discovery(format):
    """Service discovery mechanism required for Open311 APIs."""
    if format == 'json':
        return jsonify(service_discovery)
    elif format == 'xml':
        response = make_response(render_template('discovery.xml', discovery=service_discovery))
        response.headers['Content-Type'] = 'text/xml; charset=utf-8'
        return response
    else:
        abort(404)

@app.route('/services.<format>')
def service_list(format):
    """Provide a list of acceptable 311 service request types and their 
    associated service codes. These request types can be unique to the
    city/jurisdiction.
    """
    if format == 'json':
        response = make_response(json.dumps(service_types))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
    elif format == 'xml':
        response = make_response(render_template('services.xml', services=service_types))
        response.headers['Content-Type'] = 'text/xml; charset=utf-8'
        return response
    else:
        abort(404)

@app.route('/services/<service_code>.<format>')
def service_definition(service_code, format):
    """Define attributes associated with a service code.
    These attributes can be unique to the city/jurisdiction.
    """
    if service_code not in service_definitions:
        abort(404)

    if format == 'json':
        return jsonify(service_definitions[service_code])
    elif format == 'xml':
        response = make_response(render_template('definition.xml',
                                                 definition=service_definitions[service_code]))
        response.headers['Content-Type'] = 'text/xml; charset=utf-8'
        return response
    else:
        abort(404)

def format_twitter_to_311(documents):		
    cfa311docs = []
    for document in documents:
	    cfa311doc = {}
	    cfa311doc['status'] = 'open'
	    cfa311doc['address_id'] = '999'
	    cfa311doc['description'] = document['value']['text']
	    cfa311doc['service_code'] = 'CFA1'
	    cfa311doc['service_request_id'] = document['value']['id']
	    cfa311doc['updated_datetime'] = document['value']['created_at']
	    cfa311doc['address'] = document['value']['place']['full_name']
	    cfa311doc['lat'] = document['value']['geo']['coordinates'][0]
	    cfa311doc['long'] = document['value']['geo']['coordinates'][1]
	    cfa311doc['agency_responsible'] = 'fellows'
	    cfa311doc['address'] = document['value']['place']['full_name']
	    cfa311doc['media_url'] = document['value']['entities']['media'][0]['media_url_https']
	    cfa311docs.append(cfa311doc)
    return cfa311docs            
        
@app.route('/requests.<format>', methods=['GET', 'POST'])
def service_requests(format):
    """"Create service requests.
    Query the current status of multiple requests.
    """
    if format not in ('json'):
        abort(404)

    if request.method == 'POST':
        # Create service request
        g.couch.save(dict(request.form))
        if format == 'json':
            app.logger.debug('request.form= (%s)', request.form)
            return jsonify(request.form)
    else:
        # Return a list of SRs that match the query
        sr = search(request.form)
        if format == 'json':
            #response = make_response(json.dumps(srs))   
            #response = make_response(json.dumps(g.couch.get('158007579522506752')))
            docs = list(db.view('summary/all'))
            #response = make_response(json.dumps(docs))
            response = make_response(json.dumps(format_twitter_to_311(docs)))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response

@app.route('/requests/<service_request_id>.<format>')
def service_request(service_request_id, format):
    """Query the current status of an individual request."""
    result = search(request.form)
    if format == 'json':
        return jsonify(srs[0])
    elif format == 'xml':
        response = make_response(render_template('service-requests.xml', service_requests=[srs[0]]))
        response.headers['Content-Type'] = 'text/xml; charset=utf-8'
        return response
    else:
        abort(404)

@app.route('/tokens/<token>.<format>')
def token(token, format):
    """Get a service request id from a temporary token. This is unnecessary
    if the response from creating a service request does not contain a token.
    """
    abort(404)

def search(service_request):
    """Query service requests"""
    pass # Implementation specific

def save(service_request):
    """Save service request"""
    # Implementation specific.  Just return a random SR id for now
    return {'service_request_id':random.randint(1,10000)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
