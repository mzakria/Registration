from flask import Flask,render_template,flash ,redirect ,url_for ,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form ,StringField ,TextAreaField, PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

#config MySQL
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'app'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'


#init MySQL
mysql = MySQL(app)

# authorized login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'login' in session :
                return f(*args, **kwargs)
	else :
                flash('Unauthorized please login !','w3-panel w3-pale-red w3-padding-16')
		return redirect(url_for('login'))
    return decorated_function
#end of login authorized

class RegistorForm(Form):
	name = StringField('Name',[validators.Length(min=1,max=40)])
	username = StringField('Username',[validators.Length(min=1,max=40)])
	email= StringField('Email',[validators.Length(min=6,max=40)])
	password = PasswordField('Password',[
		validators.DataRequired(),
		validators.EqualTo('confirm',message='Password do not match')
		])
	confirm = PasswordField('confirm Password')

class ArticleForm(Form):
	title = StringField('Title',[validators.Length(max=120)])
	body = TextAreaField('Body',[validators.Length(min=10)])


@app.route("/")
def index():
	return render_template('index.html')

@app.route("/about")
def about():
	return render_template('about.html')

@app.route("/edit/<string:id>",methods=['POST','GET'])
@login_required
def edit(id):
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT  `title`, `auther`, `body` FROM `articles` WHERE `id`=%s ",id)
        article = cur.fetchone()
        mysql.connection.commit()
        cur.close

        form = ArticleForm(request.form)
        form.title.data = article['title']
        form.body.data = article['body']

        if request.method == 'POST' and form.validate :
            title = request.form['title']
            body = request.form['body']
            cur = mysql.connection.cursor()
            cur.execute("UPDATE `articles` SET `title`=%s,`auther`=%s,`body`=%s WHERE `id`=%s",(title,session['username'],body,id) )
            #mysql commit
            mysql.connection.commit()
            cur.close()
            flash('Article was edit successfully!','w3-panel w3-pale-green w3-padding')
            return redirect(url_for('dashboard'))
        return render_template('edit.html',form=form)

@app.route("/delete/<string:id>",methods=['POST'])
@login_required
def delete(id):
    if request.method == 'POST' :
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM `articles` WHERE `id`=%s",id )
        #mysql commit
        mysql.connection.commit()
        cur.close()
        flash('Article was delete successfully!','w3-panel w3-pale-green w3-padding')
        return redirect(url_for('dashboard'))


@app.route("/articles")
def articles():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT `id`, `title`, `auther`, `body` FROM `articles`")
    Articles = cur.fetchall()
    mysql.connection.commit()
    cur.close
    return render_template('articles.html',articles = Articles)

@app.route("/article/<string:id>/")
def article(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT `title`, `auther`, `body` FROM `articles` WHERE `id`= %s",id )
    article = cur.fetchone()
    mysql.connection.commit()
    cur.close
    return render_template('article.html',article = article)

@app.route("/dashboard",methods=['GET','POST'])
@login_required
def dashboard():

    cur = mysql.connection.cursor()
    result = cur.execute("SELECT `id`, `title`, `auther`, `body` FROM `articles`")
    article = cur.fetchall()
    mysql.connection.commit()
    cur.close

    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate :
        title = form.title.data
        body = form.body.data
        cur = mysql.connection.cursor()
	cur.execute("INSERT INTO `articles`(`title`, `auther`, `body`) VALUES (%s,%s,%s)",(title,session['username'],body))
	#mysql commit
	mysql.connection.commit()
	cur.close()
        flash('Article Added successfully!','w3-panel w3-pale-green w3-padding')
        return redirect(url_for('dashboard'))
    return render_template('dashboard.html',form=form,article=article)


@app.route("/logout")
@login_required
def logout():
	session.clear()
	flash('You are logout !','w3-panel w3-pale-green w3-padding-16')
	return redirect(url_for('login'))


@app.route("/register",methods=['GET','POST'])
def register():
	form = RegistorForm(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		username = form.username.data
		email = form.email.data
		password = sha256_crypt.encrypt(str(form.password.data))

		# create cursor

		cur = mysql.connection.cursor()
		cur.execute("INSERT INTO `users` (`name`, `username`, `password`, `email`) VALUES (%s,%s,%s,%s)",(name,username,password,email))
		#mysql commit
		mysql.connection.commit()
		cur.close()

                flash('You are registor ! You can Login','success')
                return redirect(url_for('index'))
	return render_template ('register.html',form=form)

#login code
@app.route('/login',methods=['GET','POST'])
def login():
	if request.method == 'POST':
		username = request.form['username']
		password_submit = request.form['password']
		#create DictCursor
		cur = mysql.connection.cursor()
		result =cur.execute("SELECT * FROM `users` WHERE `username`= %s ",[username])
		if result > 0:
			data = cur.fetchone()
			hash_password = data['password']

			if sha256_crypt.verify(password_submit,hash_password):
				session['login'] = True
				session['username'] = username
				flash('You Are login !','w3-panel w3-pale-green w3-padding-16')
				return redirect(url_for('dashboard'))

			else:
				error='password Not Match!'
				return render_template('login.html',error=error)
				cur.close()

		else:
			error='Username Not Match !'
			return render_template('login.html',error=error)

	return render_template('login.html')

#app main
if (__name__ == "__main__"):
	app.secret_key = 'secret123'
	app.run(debug=True)
