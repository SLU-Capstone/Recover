import os
import sys
from flask.ext.script import Manager, Server
from recover import app

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
manager = Manager(app)

# Turn on debugger by default and reloader
manager.add_command("run", Server(
    use_debugger=True,
    use_reloader=True,
    host='0.0.0.0')
                    )


@manager.command
def drop():
    from recover.models import Patient, User, PatientInvite
    PatientInvite.drop_collection()
    Patient.drop_collection()
    User.drop_collection()


if __name__ == "__main__":
    manager.run()
