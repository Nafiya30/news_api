from flask import Flask,flash,redirect,request,url_for,render_template,session,send_file,send_from_directory, request
from flask_session import Session
from flask_mysqldb import MySQL
from otp import genotp
from cmail import sendmail
import random
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from tokenreset import token
from io import BytesIO
from requests import get
from config import key
from os.path import join

app=Flask(__name__)
app.secret_key='876@#^%jh'
app.config['SESSION_TYPE']='filesystem'
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='admin'
app.config['MYSQL_DB']='news'
Session(app)
mysql=MySQL(app)
@app.route('/')
def homepage():
    return render_template('home page.html')
@app.route('/registration',methods=['GET','POST'])
def ProRegister():
    if request.method=='POST':
        name=request.form['name']
        mobile=request.form['mobile']
        email=request.form['email']
        password=request.form['password']
        cursor=mysql.connection.cursor()
        cursor.execute('select name from readers')
        data=cursor.fetchall()
        cursor.execute('SELECT email from readers')
        edata=cursor.fetchall()
            #print(data)
        if (name,) in data:
            flash('User already exists')
            return render_template('ProRegister.html')
        if (email,) in edata:
             flash('Email  already exists')
             return render_template('ProRegister.html')
        cursor.close()
        otp=genotp()
        subject='Thanks for registering to the application'
        body=f'Use this otp to register {otp}'
        sendmail(email,body,subject)
        return render_template('otp.html',otp=otp,name=name,mobile=mobile,email=email,password=password)
    return render_template('ProRegister.html')
@app.route('/ProLogin',methods=['GET','POST'])
def ProLogin():
    if session.get('user'):
        return redirect(url_for('home'))
    if request.method=='POST':
        name=request.form['name']
        password=request.form['password']
        cursor=mysql.connection.cursor()
        cursor.execute('select count(*) from  readers where name=%s and password=%s',[name,password])
        count=cursor.fetchone()[0]
        if count==0:
            flash('Invalid username or password')
            return render_template('ProLogin.html')
        else:
            session['user']=name
            return redirect(url_for('home'))
    return render_template('ProLogin.html')
@app.route('/home')
def home():
    if session.get('user'):
        return render_template('home.html')
    else:
        return redirect(url_for('ProLogin'))
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('homepage'))
    else:
        flash('already logged out')
        return redirect(url_for('ProLogin'))
    
@app.route('/otp/<otp>/<name>/<mobile>/<email>/<password>',methods=['GET','POST'])
def otp(otp,name,mobile,email,password):
    if request.method=='POST':
        uotp=request.form['otp']
        if otp==uotp:
            lst=[name,mobile,email,password]
            query='insert into readers values(%s,%s,%s,%s)'
            cursor=mysql.connection.cursor()
            cursor.execute(query,lst)
            mysql.connection.commit()
            cursor.close()
            flash('Details Registered')
            return redirect(url_for('ProLogin'))
        else:
            flash('Wrong OTP')
            return render_template('otp.html',otp=otp,name=name,mobile=mobile,email=email,password=password)       
@app.route('/forgotpassword',methods=['GET','POST'])
def forgot():
    if request.method=='POST':
        name=request.form['name']
        cursor=mysql.connection.cursor()
        cursor.execute('select name from readers')
        data=cursor.fetchall()
        if(name,) in data:
            cursor.execute('select email from readers where name=%s',[name])
            data=cursor.fetchone()[0]
            cursor.close()
            subject=f'Reset Password for {data}'
            body=f'Reset the password using-{request.host+url_for("createpassword",token=token(name,240))}'
            sendmail(data,subject,body)
            flash('Reset link sent to your mail')
            return redirect(url_for('ProLogin'))
        else:
            return 'Invalid user id'
    return render_template('forgot.html')

@app.route('/createpassword/<token>',methods=['GET','POST'])
def createpassword(token):
    try:
        s=Serializer(app.config['SECRET_KEY'])
        fid=s.loads(token)['user']
        if request.method=='POST':
            npass=request.form['npassword']
            cpass=request.form['cpassword']
            if npass==cpass:
                cursor=mysql.connection.cursor()
                cursor.execute('update news set password=%s where name=%s',[npass,name])
                mysql.connection.commit()
                return 'Password reset Successfull'
            else:
                return 'Password mismatch'
        return render_template('newpassword.html')
    except Exception as e:
        print(e)
        return 'Link expired try again'

@app.route('/1',methods=['POST','GET'])
def index():
	#print(request.remote_addr)
	response1 = get("https://newsapi.org/v2/top-headlines?country=in", params = {'apiKey' : key, 'category' : 'business'}).json()
	response2 = get("https://newsapi.org/v2/top-headlines?country=in", params = {'apiKey' : key, 'category' : 'entertainment'}).json()
	response3 = get("https://newsapi.org/v2/top-headlines?country=in", params = {'apiKey' : key, 'category' : 'general'}).json()
	response4 = get("https://newsapi.org/v2/top-headlines?country=in", params = {'apiKey' : key, 'category' : 'health'}).json()
	response5 = get("https://newsapi.org/v2/top-headlines?country=in", params = {'apiKey' : key, 'category' : 'science'}).json()
	response6 = get("https://newsapi.org/v2/top-headlines?country=in", params = {'apiKey' : key, 'category' : 'sports'}).json()
	response7 = get("https://newsapi.org/v2/top-headlines?country=in", params = {'apiKey' : key, 'category' : 'technology'}).json()
	return render_template('index.html', response1 = response1, response2 = response2, response3 = response3, response4 = response4, response5 = response5, response6 = response6, response7 = response7)

@app.route('/search', methods=['POST'])
def search():
	response = get("https://newsapi.org/v2/everything", params={'apikey' : key, 'q' : request.form['searchBar']}).json()
	return render_template('search.html', response = response)

@app.route('/sources')
def sources():
	response = get("https://newsapi.org/v2/sources", params = {'apiKey' : key}).json()
	return render_template('sources.html', name = response)

@app.route('/about')
def about():
	return render_template('about.html')
	
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
if __name__ == "__main__":
	app.run()





app.run(use_reloader=True,debug=True)
            
        





