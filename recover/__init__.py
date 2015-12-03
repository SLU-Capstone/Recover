from flask import Flask, render_template
from flask.ext.mongoengine import MongoEngine
from flask.ext.login import LoginManager

# Set up app and database connection
app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {'DB': 'tester'}
app.config['SECRET_KEY'] = 'wut'

login_manager = LoginManager()
login_manager.init_app(app)

db = MongoEngine(app)


@app.route('/')
def load_home_page():
    return render_template('home.html')


def register_blueprints(ap):
    """
    prevent circular imports by registering the blueprints.
    :param ap: app to register
    """
    from recover.view import patient_dashboard, patient_add, user_management
    ap.register_blueprint(patient_dashboard)
    ap.register_blueprint(patient_add)
    ap.register_blueprint(user_management)

register_blueprints(app)

if __name__ == '__main__':
    app.run()
