from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import request, redirect, url_for, render_template
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required
from flask_mail import Mail

# Create app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://irqgiazg:tNlIttpHWgyn54WGFUkNaZQPB3f42e7U@stampy.db.elephantsql.com:5432/irqgiazg'
app.config['SECRET_KEY'] = 'XXYwqeh6323345fweWW'
app.config['SECURITY_REGISTERABLE'] = True
app.config['DEBUG'] = True
# At top of file
# After 'Create app'
app.config['MAIL_SERVER'] = 'smtp.office365.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'michael.govoni@gexpro.com'
#dont forget to change this configuration in production
app.config['MAIL_PASSWORD'] = 'passwordholder'

# Create database connection object
db = SQLAlchemy(app)

# Define models
roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))


class Contractors(db.Model):
    idc = db.Column(db.Integer, autoincrement=True, primary_key=True)
    contname = db.Column(db.String(255), unique=True)


class Bidrecord(db.Model):
    rid = db.Column(db.Integer, autoincrement=True, primary_key=True)
    contname = db.Column(db.String, db.ForeignKey('Contractors.contname'))
    #contractor name key
    #contname from above model?
    crosell = db.Column(db.String(255), unique=True)
    appval = db.Column(db.String(255), unique=True)
    specproj = db.Column(db.String(255), boolean=True)
    comments = db.Column(db.String(1000))


# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


# Views
@app.route('/')
@login_required
def index():
    return render_template('InputPage.html')

@app.route('/profile/<email>')
@login_required
def profile(email):
    user = User.query.filter_by(email=email).first()
    return render_template('InputPage.html', user=user)

@app.route('/post_user', methods=['POST'])
def post_user():
    user = User(request.form['username'], request.form['email'])
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('index'))



if __name__ == "__main__":
    app.run('localhost')
