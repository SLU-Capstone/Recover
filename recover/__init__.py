from flask import Flask, redirect, request, jsonify
from flask.ext.mongoengine import MongoEngine

# Set up app and database connection
app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {'DB': 'tester'}
app.config['SECRET_KEY'] = 'wut'
db = MongoEngine(app)


def register_blueprints(ap):
    """prevent circular imports by registering the blueprints."""
    from recover.view import patients, register
    ap.register_blueprint(patients)
    ap.register_blueprint(register)


register_blueprints(app)

if __name__ == '__main__':
    app.run()
