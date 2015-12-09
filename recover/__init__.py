from flask import Flask, render_template
from flask.ext.login import LoginManager, current_user
from flask.ext.mongoengine import MongoEngine

# Set up app and database connection
app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {'DB': 'tester'}
app.config['SECRET_KEY'] = 'wut'

login_manager = LoginManager(app)

db = MongoEngine(app)


@app.route('/')
def load_home_page():
    return render_template('home.html', user=current_user)


def register_blueprints(ap):
    """
    prevent circular imports by registering the blueprints.
    :param ap: app to register
    """
    from recover.views.dashboard import patient_dashboard
    from recover.views.new_patient import patient_add
    from recover.views.management import user_management
    ap.register_blueprint(patient_dashboard)
    ap.register_blueprint(patient_add)
    ap.register_blueprint(user_management)


register_blueprints(app)

if __name__ == '__main__':
    app.run()
