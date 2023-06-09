from flask import Flask , render_template , flash , redirect , request , url_for , session , logging
# from data import Articles
from flask_mysqldb import MySQL 
from wtforms import Form , StringField, TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
app =  Flask(__name__)

#Config mySQL

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#init MYSQL
mysql= MySQL(app)

 
# Articles = Articles()

# index
@app.route('/')
def index():
    return render_template('home.html')

#About
@app.route('/about')
def about():
    return render_template('about.html')

#Articles
@app.route('/articles')
def articles():
# Create cursor
    cur = mysql.connection.cursor()
    
    #Get Articles
    result = cur.execute("SELECT * FROM articles")
    
    articles = cur.fetchall()
    
    if result > 0:
        return render_template('articles.html',articles = articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg = msg)
    cur.close()
    
    
#Single Article
@app.route('/article/<string:id>/')
def article(id):
    
    # Create cursor
    cur = mysql.connection.cursor()
    
    #Get Article
    result = cur.execute("SELECT * FROM articles WHERE id = %s",[id])
    
    article = cur.fetchone()
    
    return render_template('article.html', article= article)


#Register Class form

class RegisterForm(Form):
    name = StringField('Name',[validators.Length(min=1 , max=50)])
    username = StringField('Username',[validators.Length(min=4 , max=25)])
    email = StringField('Email',[validators.Length(min = 6, max = 50)])
    password = PasswordField('Password',[
        validators.DataRequired(),
        validators.EqualTo('confirm',message = 'Passwords do not match'),
    ])
    
    confirm = PasswordField('Confirm Password')
    
    # User register

@app.route('/register',methods = ['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password =sha256_crypt.hash(str(form.password.data))
        
        #Create cursor 
        cur = mysql.connection.cursor()
        
        #Execute Query
        cur.execute("INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)",(name,email,username,password))
       
        #Commit to DB
        mysql.connection.commit()
        
        #Close connection
        cur.close()
        
        flash('You are now registered and can login','Success')
        
        redirect(url_for('login'))
    return render_template('register.html',form =form)
    
#User login

@app.route('/login' , methods = ['GET',"POST"])
def login():
    if request.method == 'POST':
        #Get Form Fields
        username = request.form['username']
        password_canidate = request.form['password']
        
        #Create a Cursor
        cur=mysql.connection.cursor()
        
        #Get user by username 
        result = cur.execute("SELECT * FROM users WHERE username= %s",[username])
        
        if result > 0:
            #GET stored hash
            data = cur.fetchone()
            password = data['password']
            
            #Compare Passwords
            if sha256_crypt.verify(password_canidate,password):
                #Passed
                session['logged_in'] = True
                session['username'] = username
                
                flash('You are now logged in','success')
                return redirect(url_for('dashboard'))
                
            else:
                error = 'Invalid Login'
                return render_template('login.html' , error=error)  
            #Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html' , error = error)                
        
    return render_template('login.html') 

# Check if user logged in 
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else: 
            flash('Unauthorized , please login', 'danger')
            return redirect(url_for('login'))
    return wrap


@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out' , 'success')
    return redirect(url_for('login'))

# Dashboard 
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()
    
    #Get Articles
    result = cur.execute("SELECT * FROM articles")
    
    articles = cur.fetchall()
    
    if result > 0:
        return render_template('dashboard.html',articles = articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg = msg)
        cur.close()


# Article Form class
class ArticleForm(Form):
    title = StringField('Title',[validators.Length(min=1 , max=200)])
    body = TextAreaField('Body',[validators.Length(min=1)])
  

# Add Article 
@app.route('/add_article', methods = ['POST' , 'GET'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data
        
        # Create Cursor
        cur = mysql.connection.cursor()
        
        #Execute
        cur.execute("INSERT INTO articles(title,body,author) VALUES(%s,%s,%s)", (title,body,session['username']))
        
        # Commit to DB
        mysql.connection.commit()
        
        #Close connection 
        cur.close()
        
        flash('Article Created' ,'success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html',form=form)



# Edit Article 
@app.route('/edit_article/<string:id>', methods = ['POST' , 'GET'])
@is_logged_in
def edit_article(id):
    
        # Create Cursor
    cur = mysql.connection.cursor()
    
    # GET article BY ID 
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])
    
    article = cur.fetchone()
    
    # GET form
    form = ArticleForm(request.form)
    
    # Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']
    
    
    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']
        
        # Create Cursor
        cur = mysql.connection.cursor()
        
        #Execute
        cur.execute("UPDATE articles SET title = %s ,body = %s  WHERE id = %s and author = %s  ", (title ,body,id , session['username'] ))
        
        # Commit to DB
        mysql.connection.commit()
        
        #Close connection 
        cur.close()
        return redirect(url_for('dashboard'))
    return render_template('edit_article.html',form=form)

    
@app.route('/delete_article/<string:id>', methods = ['POST'])
@is_logged_in
def delete_article(id):
    cur= mysql.connection.cursor()
    
    cur.execute("DELETE FROM articles WHERE id=%s ", [id])
    
    cur.close()
    
    mysql.connection.commit()

     
    flash('Article DELETED' ,'success')
    return redirect(url_for('dashboard'))


    # ResetPassword
# @app.route('/resetPassword',methods = ['GET','POST'])
# def resetPassword():
#     form = RegisterForm(request.form)
#     if request.method == 'POST' and form.validate():
#         email = form.email.data
#         password =sha256_crypt.hash(str(form.password.data))
        
#         #Create cursor 
#         cur = mysql.connection.cursor()
        
#         #Execute Query
#         cur.execute("UPDATE users SET password = %s  WHERE email = %s ",(password,email))
       
#         #Commit to DB
#         mysql.connection.commit()
        
#         #Close connection
#         cur.close()
        
#         flash('You Updated your password','Success')
        
#         redirect(url_for('login'))
#     return render_template('reset_password.html',form = form)
    
    

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)