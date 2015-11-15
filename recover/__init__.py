from flask import Flask
from flask.ext.mongoengine import MongoEngine

# Set up app and database connection
app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {'DB': 'tester'}
app.config['SECRET_KEY'] = 'wut'
db = MongoEngine(app)


def register_blueprints(ap):
    """prevent circular imports by registering the blueprints."""
    from recover.view import patients
    ap.register_blueprint(patients)


register_blueprints(app)

if __name__ == '__main__':
    app.run()
