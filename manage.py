import os
import sys
from flask.ext.script import Manager, Server
from recover import app

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
manager = Manager(app)

# Turn on debugger by default
manager.add_command("run", Server(
    use_debugger=True,
    use_reloader=True,
    host='0.0.0.0'))


@manager.command
def doc():
    os.chdir('doc')
    os.system('make html > /dev/null 2>&1')
    print 'html documentation is in doc/_build/html/'
    os.system('make latexpdf >/dev/null 2>&1')
    print 'latex and pdf documentation is in doc/_build/latex/'
    os.chdir('..')
    os.system('cp -r doc/_build/html/ recover/static/doc/')


@manager.command
def midnight():
    from scripts.midnightRun import midnight_run
    midnight_run()


@manager.command
def drop():
    from recover.models import Patient, User, PatientInvite
    PatientInvite.drop_collection()
    Patient.drop_collection()
    User.drop_collection()


if __name__ == "__main__":
    manager.run()
