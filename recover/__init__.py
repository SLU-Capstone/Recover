import os
from celery import Celery
from flask import Flask, render_template
from flask.ext.login import LoginManager, current_user
from flask.ext.mongoengine import MongoEngine
from flask_moment import Moment

# Set up app and database connection
app = Flask(__name__, static_folder='static')
app.config['MONGODB_SETTINGS'] = {'DB': 'tester'}
app.config['SECRET_KEY'] = 'wut'
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
JSON_FOLDER = os.path.join(APP_ROOT, 'static/recover_export_data')
app.config['JSON_FOLDER'] = JSON_FOLDER + '/'
app.config['INFO'] = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + '/log/'
app.config['PROPAGATE_EXCEPTIONS'] = True


def make_celery(app):
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery

app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']
)
celery = make_celery(app)

login_manager = LoginManager(app)

db = MongoEngine(app)

moment = Moment(app)


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
