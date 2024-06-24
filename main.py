from flask import Flask,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from werkzeug.utils import secure_filename
import json
import os
import math
from datetime import datetime


with open('config.json', 'r') as configfile:
    params = json.load(configfile)["params"]

app = Flask(__name__)
app.secret_key = 'the-random-string'
app.config['UPLOAD_FOLDER'] = params['upload_location']

app.config.update(
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_PORT = "465",
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-psw']
)
mail = Mail(app)

local_server = params['local_server']
if local_server:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['prod_uri']

db = SQLAlchemy(app)

class Contacts(db.Model):
    '''
    sno, name, email, phone_num, mes, date
    '''
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    mes = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)

class Posts(db.Model):
    '''
    sno, name, email, phone_num, mes, date
    '''
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    tagline = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(20), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    img_file = db.Column(db.String(12), nullable=True)
    date = db.Column(db.String(12), nullable=True)

@app.route('/')
def home():

    myposts = Posts.query.filter_by().all()
    last = math.ceil(len(myposts)/int(params['no_of_posts']))
    page = request.args.get('page')

    if (not str(page).isnumeric()):
        page = 1

    page = int(page)
    myposts = myposts[ (page-1) * int(params['no_of_posts']) : (page-1) * int(params['no_of_posts']) + int(params['no_of_posts']) ]
    if page == 1:
        prev = "#"
        next = '/?page=' + str(page + 1)
    elif page == last:
        prev = '/?page=' + str(page - 1)
        next = "#"
    else:
        prev = '/?page=' + str(page - 1)
        next = '/?page=' + str(page + 1)

    return render_template('index.html',param=params,posts=myposts,prev=prev,next=next)


@app.route('/post/<string:post_slug>',methods=['GET'])
def post_route(post_slug):
    mypost = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html',param=params,post=mypost)

@app.route('/dashboard', methods=['GET', 'POST'])
def login():
    if 'user' in session and session['user'] == params['admin_user']:
        myposts = Posts.query.all()
        return render_template('dashboard.html',param=params,posts=myposts)

    if request.method == 'POST':
        username = request.form.get('uname')
        userpsw = request.form.get('pass')
        if (username == params['admin_user'] and userpsw == params['admin_psw']):
            session['user'] = username
            myposts = Posts.query.all()
            return render_template('dashboard.html',param=params,posts=myposts)

    return render_template('login.html',param=params)

@app.route('/edit/<string:sno>', methods=['GET', 'POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            entered_title = request.form.get('title')
            entered_tagline = request.form.get('tline')
            entered_slug = request.form.get('slug')
            entered_content = request.form.get('content')
            entered_img_file = request.form.get('img_file')
            date = datetime.now()

            if sno == "0":
                post = Posts(title=entered_title,tagline=entered_tagline,slug=entered_slug,content=entered_content,img_file=entered_img_file,date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = entered_title
                post.tagline = entered_tagline
                post.slug = entered_slug
                post.content = entered_content
                post.img_file = entered_img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/'+sno)

        post = Posts.query.filter_by(sno=sno).first()

        return render_template('edit.html',param=params,post=post)

@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route('/uploader', methods = ['GET', 'POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            f = request.files['filename']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename) ))
            return "file uploaded successfully"

@app.route('/delete/<string:sno>', methods=['GET', 'POST'])
def delete(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')



@app.route('/about')
def about():
    return render_template('about.html',param=params)


@app.route('/contact', methods = ['GET', 'POST'])
def contact():
    if (request.method == 'POST'):
        '''Add entry to the database'''
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('e-mail')
        message = request.form.get('message')

        entry = Contacts(name=name,email=email,phone_num=phone,mes=message,date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from '+name,
                          sender=email,
                          recipients=[params['gmail-user']],
                          body=message+"\n"+phone
                          )
    return render_template('contact.html', param=params)

if __name__ == '__main__':
    app.run(debug=True)