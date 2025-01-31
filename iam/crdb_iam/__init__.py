import secrets
import psycopg2
import configparser
from flask import Flask, current_app
from flask_bootstrap import Bootstrap5
from flask_wtf import CSRFProtect
from crdb_iam import pages

def create_app():
    
    app = Flask(__name__)

    app.register_blueprint(pages.bp)
    bootstrap = Bootstrap5(app)        # Bootstrap-Flask requires this line
    csrf = CSRFProtect(app)            # Flask-WTF requires this line

    # read the configuration file 
    config = configparser.ConfigParser()
    config.read('config.ini')

    # assign application config variables read from the config.ini file
    app.config['SECRET_KEY'] = secrets.token_urlsafe(16)
    app.config['HOST_IP'] = config['database']['host_ip']
    app.config['PORT_NUM'] = config['database']['port_num']

    return app                         # return the app
