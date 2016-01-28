from flask import Blueprint, request, flash, render_template, redirect
from flask.ext.login import login_user, login_required, current_user, logout_user
from mongoengine import DoesNotExist
from recover import login_manager
from recover.forms.UserRegistrationForm import UserRegistrationForm
from recover.models import User

user_management = Blueprint('user_management', __name__, template_folder='../templates')


@user_management.route('/register/', methods=['GET', 'POST'])
def register():
    """
    Registers a Physician to use our system. Physicians will be required to
    enter a user name, email address, password, and confirm their password.
    """
    form = UserRegistrationForm(request.form)
    if request.method == 'POST':
        try:
            if User.objects(email=form.email.data).count() > 0:
                flash("A user with that email already exists. Please try again.", 'warning')
                return render_template('register.html', form=form)
        except AttributeError:
            pass  # Users table is empty, so no need to check.

        if form.validate():
            new_user = User(username=form.username.data, email=form.email.data)
            new_user.set_password(form.password.data)
            new_user.save()
            flash("User registration successful. You can now login above.", 'success')
            return redirect('/')
        else:
            flash("Invalid input: please see the suggestions below.", 'warning')
    return render_template('register.html', form=form)


@user_management.route('/login', methods=['POST'])
def login():
    """
    The checks a users email with a password hash and if successful, allows the
    user to log into our system. If unsuccessful, the user is redirected to the
    home page with a warning.
    """
    email = request.form['email']
    login_unsuccessful = "Login failed: Invalid email or password. Please try again."

    try:  # User with given email does not exist
        user = User.objects.get(email=email)
    except DoesNotExist:
        flash(login_unsuccessful, 'warning')
        return redirect('/')

    if user.check_password(request.form['password']):
        login_user(user)
        message = "Welcome, " + user.username + "!"
        flash(message, 'success')
        return redirect('/dashboard')

    flash(login_unsuccessful, 'warning')
    return redirect('/')


@user_management.route('/logout')
@login_required
def logout():
    """
    User becomes unauthenticated and logs him or her off of our system.
    """
    user = current_user
    user.authenticated = False
    user.save()
    logout_user()
    return redirect('/')


@login_manager.user_loader
def load_user(email):
    """
    Loads a user after successfully logging into the system.
    """
    user = User.objects(email=email)
    if user.count() == 1:
        return user[0]
    return None


@login_manager.unauthorized_handler
def unauthorized():
    """
    Redirects users who attempt to access pages that they must strictly
    be logged on to in order to access.
    """
    # customize message shown for unauthorized route access.
    flash("Unauthorized resource: You'll first need to login to do that.", 'warning')
    return redirect('/')


# Admin section #
from recover.forms import AdminViewer

@user_management.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if str(current_user) != 'admin':
        flash('Error: Restricted Access', 'warning')
        return redirect('/')
    userForms = []
    for user in User.objects():
        form = AdminViewer.AdminUsers(request.form, [user.username, user.email])
        form.username.data = user.username
        form.email.data = user.email
        userForms.append(form)
    patientForm = AdminViewer.AdminPatients(request.form)
    if request.method == 'POST':
        flash("User update successful. lol, jk. Not implemented yet.", 'success')
        return redirect('/admin')
    return render_template('admin.html', userForms=userForms)
