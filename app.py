from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import request, redirect, url_for, render_template
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required
from flask_mail import Mail

# Create app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://flask:auMkG62SDnbY7A9L@postgres-1.cf8xu3xji3wp.us-east-1.rds.amazonaws.com/salesadmin'
app.config['SECRET_KEY'] = 'XXYwqeh6323345fweWW'
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_PASSWORD_HASH'] = 'bcrypt'
app.config['SECURITY_PASSWORD_SALT'] = '$2a$16$PnnIgfMwkOjGX4SkHqSOPO'
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
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('user', lazy='dynamic'))


bidrecords_contractors = db.Table('bidrecords_contractors', db.metadata,
    db.Column('bidrecord_id', db.Integer, db.ForeignKey('bidrecord.id')),
    db.Column('contractor_id', db.Integer, db.ForeignKey('contractor.id'))
)

class Bidrecord(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uid = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String)
    biddate = db.Column(db.DateTime())
    crosell = db.Column(db.String(255))
    appval = db.Column(db.String(255))
    specproj = db.Column(db.String(255))
    comments = db.Column(db.String(255))
    contractors = db.relationship("Contractor", secondary=bidrecords_contractors)


class Contractor(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)


# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


"""""
# First Run / Init
@app.before_first_request
def create_db():
    db.create_all()
    # Pre-populate Contractors
    contractor = Contractor.query.first()
    if contractor is None:
        db.session.add(Contractor(name="Company Name 1", email="email1@host.com"))
        db.session.add(Contractor(name="Company Name 2", email="email2@host.com"))
        db.session.add(Contractor(name="Company Name 3", email="email3@host.com"))
        db.session.add(Contractor(name="Company Name 4", email="email4@host.com"))
        db.session.add(Contractor(name="Company Name 5", email="email5@host.com"))
        db.session.commit()
    # Create Admin
    user = User.query.first()
    if user is None:
        user_datastore.create_user(email='kendog@gmail.com', password='123456')
        db.session.commit()
"""""


# Views
@app.route('/')
@login_required
def index():
    return redirect(url_for('rfq'))


@app.route('/rfq')
@login_required
def rfq():
    contractors = Contractor.query.all()
    return render_template('rfq_form.html', contractors=contractors)


@app.route('/rfq/post', methods=['POST'])
@login_required
def rfq_post():
    name = request.form.get('name')
    biddate = request.form.get('biddate')
    crosell = request.form.getlist('crosell')
    appval = request.form.get('appval')
    comments = request.form.get('comments')
    uid = request.form.get('uid')

    if bool(request.form.get('specproj')):
        specproj = "Yes"
    else:
        specproj = "No"

    bidrecord = Bidrecord(name=name, uid=uid, biddate=biddate, crosell=crosell, appval=appval, specproj=specproj, comments=comments)

    contractors = request.form.getlist('contractors')
    for cid in contractors:
        bidrecord.contractors.append(Contractor.query.filter_by(id=cid).first())

    db.session.add(bidrecord)
    db.session.commit()
    return redirect(url_for('rfq_table'))


@app.route('/rfq/<id>')
@login_required
def rfq_details(id):
    bidrecord = Bidrecord.query.filter_by(id=id).first()
    user = User.query.filter_by(id=bidrecord.uid).first()
    return render_template('rfq_details.html', bidrecord=bidrecord, user=user)


@app.route('/rfq/table')
@login_required
def rfq_table():
    bidrecords = Bidrecord.query.all()
    return render_template('rfq_table.html', bidrecords=bidrecords)


@app.route('/rfq/calendar')
@login_required
def rfq_calendar():
    bidrecords = Bidrecord.query.all()
    return render_template('rfq_calendar.html', bidrecords=bidrecords)


@app.route('/contractor')
@login_required
def contractor_form():
    return render_template('contractor_form.html')


@app.route('/contractor/post', methods=['POST'])
def contractor_post():
    if 'submit-add' in request.form:
        contractor = Contractor(name=request.form['name'], email=request.form['email'])
        db.session.add(contractor)
        db.session.commit()
        return redirect(url_for('contractor_list'))
    if 'submit-edit' in request.form:
        exists = db.session.query(Contractor.id).filter_by(id=request.form['id']).scalar()
        if exists:
            contractor = Contractor.query.filter_by(id=request.form['id']).first()
            contractor.name = request.form['name']
            contractor.email = request.form['email']
            db.session.commit()
        return redirect(url_for('contractor_list'))


@app.route('/contractor/<id>')
@login_required
def contractor_profile(id):
    contractor = Contractor.query.filter_by(id=id).first()
    return render_template('contractor_edit.html', contractor=contractor)


@app.route('/contractor/list')
@login_required
def contractor_list():
    contractors = Contractor.query.all()
    return render_template('contractor_list.html', contractors=contractors)



if __name__ == "__main__":
    app.run('localhost')
