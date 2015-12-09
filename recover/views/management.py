from flask import Blueprint, request, flash, render_template, redirect
from flask.ext.login import login_user, login_required, current_user, logout_user
from mongoengine import DoesNotExist
from recover import login_manager
from recover.forms.UserRegistrationForm import UserRegistrationForm
from recover.models import User

user_management = Blueprint('user_management', __name__, template_folder='../templates')


@user_management.route('/register/', methods=['GET', 'POST'])
def register():
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
    user = current_user
    user.authenticated = False
    user.save()
    logout_user()
    return redirect('/')


@login_manager.user_loader
def load_user(email):
    user = User.objects(email=email)
    if user.count() == 1:
        return user[0]
    return None


@login_manager.unauthorized_handler
def unauthorized():
    # customize message shown for unauthorized route access.
    flash("Unauthorized resource: You'll first need to login to do that.", 'warning')
    return redirect('/')

