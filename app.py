from flask import Flask, request, render_template, redirect, session, flash, jsonify
import json
from flask_debugtoolbar import DebugToolbarExtension
from flask_bcrypt import Bcrypt
from secrets import API_SECRET_KEY
from fileread import FileRead
import requests
import pprint
from classes import BillSearch
from models import db, connect_db, Bill, PolicyArea, User, BillFollows, Member, Session, Party, State
from forms import BillForm, SignupForm, LoginForm, LegislatorForm
from secrets import API_SECRET_KEY
from sqlalchemy import and_



headers = {'X-API-Key': API_SECRET_KEY}

pp = pprint.PrettyPrinter(indent=4)


ROWS_PER_PAGE = 10


app = Flask(__name__)
app.config['SECRET_KEY'] = "oh-so-secret"
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///lumine'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

connect_db(app)
debug = DebugToolbarExtension(app)


@app.route('/')
def show_home_page():

    if session.get('username', False):

        return redirect('/dashboard')

    else:

        return render_template('index.html')

@app.route('/get-policy-areas')
def get_policy_areas():

    policy_areas = PolicyArea.query.all()

    policy_areas = [{'id': policy_area.id,'name':policy_area.name} for policy_area in policy_areas]

    return jsonify(policy_areas)

@app.route('/bills', methods=['GET'])
def view_bills():
    policy_areas = db.session.query(PolicyArea.id,PolicyArea.name).all()
    sessions = db.session.query(Session.id).all()
    
    pas = [('','Any Subject') ]

    for policy_area in policy_areas:

        pas.append(policy_area)

    filter_args = []

    # unpack tuple into list
    s = [session[0] for session in sessions]

    form = BillForm(request.args)
    form.policy_area.choices = pas
    form.session.choices = s

    page = request.args.get('page', 1, type=int)

    # subject
    if request.args.get('policy_area',False):
        policy_area_id = request.args['policy_area']
        policy_area = PolicyArea.query.get_or_404(policy_area_id)
        filter_args.append(Bill.primary_subject == policy_area.name )

    # session
    if request.args.get('session',False):
        session_id=request.args['session']
        filter_args.append(Bill.congress == session_id)
    else:
        session_id='116'
        filter_args.append(Bill.congress == session_id)

    #start date/ end date
    if request.args.get('start-date',False):
        start_date = request.args['start-date']
        filter_args.append(Bill.introduced_date >= start_date)
    else:
        start_date=''

    if request.args.get('end-date',False):
        end_date = request.args['end-date']
        filter_args.append(Bill.introduced_date <= end_date)
    
    else:
        end_date=''

    bills = Bill.query.filter(and_(*filter_args)).paginate(page=page, per_page=10)
    return render_template('bills/bills.html', policy_areas=policy_areas, sessions=sessions, form=form, bills=bills, start_date=start_date, end_date=end_date)

@app.route('/bills/<bill_id>')
def view_bill(bill_id):

    bill = Bill.query.get_or_404(bill_id)

    # bill = Bill.query.filter(Bill.bill_slug==bill_slug).one_or_none()

    if bill:

        summary = prune_summary(bill.summary)
    
        return render_template("bills/single_bill.html", bill=bill, summary=summary)

@app.route('/bill/<bill_id>/follow', methods=['POST'])
def follow_bill(bill_id):

    if session.get('username', False):

        bill = BillFollows.query.filter(BillFollows.bill_id == bill_id and BillFollows.username == session['username']).one_or_none()

        if bill:

            db.session.delete(bill)
            db.session.commit()
            return jsonify({'resp_code': 'unfoll_success'})

        
        else:
            new_bill_follow = BillFollows(bill_id = bill_id, username=session['username'])
            db.session.add(new_bill_follow)
            db.session.commit()
            return jsonify({'resp_code': 'foll_success'})

    else:
        # flash('You must be logged in to do that!')
        return jsonify({'resp_code': 'not_logged_in'})

@app.route('/legislators')
def view_legislators():

    form = LegislatorForm(request.args)
    filter_args = []

    parties = db.session.query(Party.code,Party.name).all()
    states = db.session.query(State.acronym,State.name).all()

    # make a function
    for party in parties:

        form.party.choices.append(party)

    for state in states:

        form.state.choices.append(state)  


    page = request.args.get('page', 1, type=int)

    if request.args.get('state',False) and request.args.get('state') != '0':

        state_code = request.args['state']
        filter_args.append(Member.state_id == state_code)

    if request.args.get('party',False) and request.args.get('party') != '0':

        party_code = request.args['party']
        filter_args.append(Member.party_id == party_code)

    if request.args.get('chamber',False) and request.args.get('chamber') != '0':

        position_code = request.args['chamber']
        filter_args.append(Member.position_code == position_code)

    # filter out member in office or add select option
    # filter_args.append(Member.in_office==True)
    legislators = Member.query.filter(and_(*filter_args)).paginate(page=page, per_page=10)

    return render_template('legislators/legislators.html', members = legislators, form=form)

@app.route('/legislator/<legislator_id>')
def view_legislator(legislator_id):


    legislator = Member.query.filter(Member.id==legislator_id).first()

    sponsored_bills = legislator.sponsored_bills

    return render_template('legislators/single_legislator.html', legislator = legislator, sponsored_bills=sponsored_bills)


# a page to give information on the chambers/ scronyms etc, mostly will be done in js dropping and revealing information
@app.route('/learn')
def view_learn_page():


    return render_template('learn.html')


@app.route('/dashboard')
def show_homepage():

    if session.get('username', False):

        user = User.query.filter(User.username==session['username']).one_or_none()
        return render_template('user/dashboard.html', user=user, bills=user.followed_bills)

    else:
        flash('No user logged in')
        return redirect('/')

@app.route('/profile')
def show_profile():

    if session.get('username', False):


        user = User.query.filter(User.username==session['username']).first()

        return render_template('user/profile.html', user=user)

    else:
        flash('No user logged in')
        return redirect('/')



@app.route('/signup', methods=['GET','POST'])
def signup():

    form = SignupForm()

    if form.validate_on_submit():

        new_user = User.register(username = form.username.data, password = form.password.data, email = form.email.data)

        db.session.add(new_user)
        db.session.commit()

        session['username'] = new_user.username

        flash(f'New user: {new_user.username} added!')

        return redirect('/dashboard')

    else:
        return render_template('user/signup.html', form=form)


@app.route('/login', methods=['GET','POST'])
def login():

    form = LoginForm()

    if form.validate_on_submit():

        user = User.authenticate(username = form.username.data, password = form.password.data)

        if user:

            session['username'] = user.username
            flash(f'User: {user.username} authenticated!')

            return redirect('/dashboard')
        
        else:
            flash('User not authenticated!')
            return redirect('/login')

    else:
        return render_template('user/login.html', form=form)

@app.route('/logout')
def logout():

    if session.get('username', False):
        session.pop('username')

        flash('Successfully logged out!')
        return redirect('/')
    
    else:
        flash('No user logged in')
        return redirect('/')

#temporary fix for api keeping title awkwardly in summary, will update full database eventually
def prune_summary(summary):

    if 'This bill' in summary:

        find_index = summary.find('This bill')
        
        lst = summary[find_index::]

        # print('Pruned summary: ', lst)

        new_summary = str(lst)

        return new_summary
    
    else:

        return summary


app.jinja_env.globals.update(prune_summary=prune_summary)


def get_bills(bill_ids):

    bills = []

    for bill_id in bill_ids:

        bill = Bill.query.filter(Bill.id == bill_id[0]).one_or_none()

        bills.append(bill)

    
    return bills