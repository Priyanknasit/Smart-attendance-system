from flask import Flask, render_template,request,redirect,url_for,flash
from flask_responses.responses import json_response
import os
from werkzeug import secure_filename
import sqlite3
from create_student import add
from run_faces import take_attendence
from run_faces import take_attendence_image
from add_courses import add_cou
from add_student_courses import add_s_courses
import json
import plotly
import pandas as pd
from passlib.hash import sha256_crypt
from joblib import *
#from werkzeug.contrib.fixers import ProxyFix


ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
app = Flask(__name__)
app.secret_key = 'super secret key'
app.config['logged_in']=False
#app.wsgi_app = ProxyFix(app.wsgi_app)

def allowed_file(filename):
    return '.' in filename and filename.split('.')[-1].lower() in ALLOWED_EXTENSIONS

#UPLOAD_FOLDER = './train_img'
#app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
@app.route('/hello', methods=['GET','POST'])
#@app.route('/hello/<name>', methods=['GET','POST']
def hello(name=None):
	if app.config['logged_in']==False:
		flash('Please log in to see this page','danger')
		return redirect(url_for('home'))
	print('wwww')
	if request.method == 'POST':
		print('asdadadas')
		files = request.files.getlist('file[]')
		name = request.form['name']
		Id = request.form['id']
		new_name = []
		count = 0
		directory = './train_img/'+str(Id)
		os.makedirs(directory)
		filecount=0
		for file in files:
			filecount+=1
			if file and allowed_file(file.filename):
				filename = secure_filename(request.form['id']+str(filecount)+'.'+file.filename.rsplit('.', 1)[1].lower())
				print(filename)
				file.save(os.path.join(directory, filename))
		add(Id,"\""+ name+"\"")
		flash('Student Successfully added','success')
		return redirect(url_for('new_home'))
	else :
		print(';ddasda')
		return render_template('new_home.html', name=name)

UPLOAD_FOLDER_IMAGE = 'Image'
ALLOWED_EXTENSIONS_IMAGE = set(['png','jpg','jpeg'])
app.config['UPLOAD_FOLDER_IMAGE'] = UPLOAD_FOLDER_IMAGE

def allowed_image(filename):
    return '.' in filename and filename.split('.')[-1].lower() in ALLOWED_EXTENSIONS_IMAGE
@app.route('/image', methods=['GET','POST'])
def image(name=None):
	if app.config['logged_in']==False:
		flash('Please log in to see this page','danger')
		return redirect(url_for('home'))
	print('working')
	if request.method == 'POST':
		print('in')
		file = request.files['file']
		if file:print(file.filename)
		date = str(request.form['date'])
		course = str(request.form.get('selected_course'))
		print('still working')
		if file and allowed_image(file.filename):
			filename = secure_filename(date+'.'+file.filename.split('.')[-1].lower())
			file.save(os.path.join(app.config['UPLOAD_FOLDER_IMAGE'], filename))
			filename = os.path.join(app.config['UPLOAD_FOLDER_IMAGE'], filename)
			found_ids = take_attendence_image(date,filename,course)
			flash('Image successfully proccessed','success')
			return redirect(url_for('json12',found=found_ids))
			#return redirect(url_for('new_home'))
	else:
		conn = sqlite3.connect('student.db')
		cursor = conn.execute('select id from courses')
		courses = []
		for row in cursor:
			courses.append(row[0])
		conn.close()
		return render_template('video.html', name=name,courses = courses)


UPLOAD_FOLDER_VIDEO = 'Video'
ALLOWED_EXTENSIONS_VIDEO = set(['mp4','avi','3gp','mkv','mov'])
app.config['UPLOAD_FOLDER_VIDEO'] = UPLOAD_FOLDER_VIDEO



def string(string_to_edit):
	return "\""+str(string_to_edit)+"\""

@app.route('/new_home', methods=['GET','POST'])
def new_home(name=None):
	'''if app.config['logged_in']==False:
		flash('Please log in to see this page','danger')
		return redirect(url_for('home'))'''
	conn = sqlite3.connect('student.db')
	cursor = conn.execute('select id from courses')
	courses = []
	for row in cursor:
		courses.append(row[0])
	cursor = conn.execute('select id from details')
	ids = []
	for row in cursor:
		ids.append(row[0])
	conn.close()
	return render_template('new_home.html',name=name, courses=courses, ids=ids)

@app.route('/', methods=['GET','POST'])
def home(name=None):
	if app.config['logged_in']==True:
		flash('You are already logged in','success')
		return redirect(url_for('new_home'))
	if request.method=='POST':
		print('working')
		if request.form['find']=='signup':
			if(request.form['password']!=request.form['c_password']):
				flash('passwords not same','danger')
				print('working')
				return redirect(url_for('home'))

			conn = sqlite3.connect('student.db')
			username = string(request.form['username'])
			fname = string(request.form['first_name'])
			lname = string(request.form['last_name'])
			id_no = string(request.form['id_no'])
			password = string(sha256_crypt.hash(str(request.form['password'])))
			conn.execute("insert into faculty_details(username,password,id,fname,lname)\
				values(%s,%s,%s,%s,%s)" %(username,password,id_no,fname,lname))
			conn.commit()
			conn.close()
			flash('User succesfully created Please login to continue','success')
			return redirect(url_for('home'))
		else:
			username = str(request.form['username'])
			password = str(request.form['password'])
			conn = sqlite3.connect('student.db')
			cursor = conn.execute("select username,password from faculty_details")
			valid = False
			for row in cursor:
				if row[0]==username and sha256_crypt.verify(password,row[1]):
					valid = True
			if valid == True:
				flash('Login Successfull','success')
				app.config['logged_in']=True
				return redirect(url_for('new_home'))
			else:
				flash('Invalid Credentials','danger')
				return redirect(url_for('home'))
	else:
		conn = sqlite3.connect('student.db')
		cursor = conn.execute('select id from courses')
		courses = []
		for row in cursor:
			courses.append(row[0])
		cursor = conn.execute('select id from details')
		ids = []
		for row in cursor:
			ids.append(row[0])
		conn.close()
		return render_template('home.html',courses=courses,ids=ids,name=None)


@app.route('/authenticate/<username>/<password>', methods=['GET','POST'])
def home1(username=None,password=None):
	print("here")
	username = str(username)
	password = str(password)
	conn = sqlite3.connect('student.db')
	cursor = conn.execute("select username,password from faculty_details")
	valid = False
	for row in cursor:
		if row[0]==username and sha256_crypt.verify(password,row[1]):
			valid = True
	print("here")
	if valid == True:
		flash('Login Successfull','success')
		app.config['logged_in']=True
		return json_response({'msg': "True"}, status_code=200)
	else:
		flash('Invalid Credentials','danger')
		return json_response({'msg': "False"}, status_code=200)



@app.route('/add_course', methods=['GET','POST'])
def add_course(name=None):
	if app.config['logged_in']==False:
		flash('Please log in to see this page','danger')
		return redirect(url_for('home'))
	if request.method == 'POST':
		id = request.form['id']
		name = request.form['name']
		prof_name = request.form['prof_name']
		add_cou(id, name, prof_name)
		flash('Course Successfully added','success')
		return redirect(url_for('new_home'))
	else :
		return redirect(url_for('new_home'))

@app.route('/attendence', methods=['GET','POST'])
def attendence(name=None):
	conn = sqlite3.connect('student.db')
	cursor = conn.execute('select id from courses')
	courses = []
	for row in cursor:
		courses.append(row[0])
	conn.close()
	return render_template('attendence.html',name=name, courses=courses)

@app.route('/add_stud_course', methods=['GET','POST'])
def add_stud_course(name= None):
	if app.config['logged_in']==False:
		flash('Please log in to see this page','danger')
		return redirect(url_for('home'))
	if request.method == 'GET':
		conn = sqlite3.connect('student.db')
		cursor = conn.execute('select id from courses')
		courses = []
		for row in cursor:
			courses.append(row[0])
		cursor = conn.execute('select id from details')
		ids = []
		for row in cursor:
			ids.append(row[0])
		conn.close()
		return render_template('add_stud_course.html',name=name, courses=courses, ids=ids)

	else:
		id = request.form.get('id')
		selected_courses = request.form.getlist('selected_courses')
		add_s_courses(id,selected_courses)
		flash('Courses for %s are successfully added'%(id),'success')
		return redirect(url_for('new_home'))

@app.route('/details', methods=['GET'])
def details(name=None):
	conn = sqlite3.connect('student.db')
	df = pd.read_sql_query("select name,id from details",conn)
	conn.close()
	df['Courses']=""
	with open ('Data/details.json') as data_file:
		data = json.load(data_file)
	for (i,row) in df.iterrows():
		if str(row['id']) in data:
			df.at[i,'Courses'] = data[str(row['id'])]
	return render_template('details.html',table=df.to_html(index=False),title='details',logged_in=str(app.config['logged_in']))

@app.route('/logout', methods=['GET','POST'])
def logout(name=None):
	app.config['logged_in'] = False
	flash('You have succesfully Logged out','success')
	return redirect(url_for('home'))

@app.route('/attendenceBy/<year>/<month>/<date>', methods=['GET','POST'])
def attendenceBy(year=None,month=None,date=None):
	conn = sqlite3.connect('student.db')
	s = "select id,\""+year+"-"+month+"-"+date+"\" from attendence1"
	print (s)
	cursor = conn.execute(s)
	da = []
	for row in cursor:
		da.append(list(row))
		print(row)
		print(da)
	conn.close()
	return json_response({"data":da},status_code=200)


@app.route('/getMail', methods=['GET','POST'])
def getMail():
	conn = sqlite3.connect('student.db')
	s = "select * from email order by id"
	cursor = conn.execute(s)
	data=[]
	for d in cursor:
		data.append(list(d))
	conn.close()
	return json_response({"mail": data},status_code=200)



@app.route('/attendenceByMonth/<month>', methods=['GET','POST'])
def attendenceByMonth(month=None):
	conn = sqlite3.connect('student.db')
	dates=["01","02","03","04","05","06","07","08","09","10","11","12","13","14","15","16","17","18","19","20","21","22","23","24","25","26","27","28"]

	dataaa=[0,0,0,0,0,0]

	for date in dates:
		s = "select id,\"2016-"+month+"-"+date+"\" from attendence1 order by id"
		print (s)
		cursor = conn.execute(s)
		for row in cursor:
			list(row)
			if row[0]==26 and row[1]==1:
				dataaa[1]+=1
			elif row[0]==46 and row[1]==1:
				dataaa[3]+=1
			elif row[0]==50 and row[1]==1:
				dataaa[4]+=1
			elif row[0]==51 and row[1]==1:
				dataaa[5]+=1
			elif row[0]==20 and row[1]==1:
				dataaa[0]+=1
			elif row[0]==45 and row[1]==1:
				dataaa[2]+=1
			print(row)
	print(dataaa)
	conn.close()
	return json_response({"20":dataaa[0],"26": dataaa[1],"45":dataaa[2],"46":dataaa[3],"50":dataaa[4],"51":dataaa[5]},status_code=200)



@app.route('/show_attendence', methods=['GET','POST'])
def show_attendence(name=None):
	if request.method == 'POST':
		#print(request.form['courses'])
		selected_course = request.form.get('selected_course')
		attendence_file = "Data/attendence"+selected_course+".json"
		attendence_csv = "CSV/attendence"+selected_course+".csv"
		with open (attendence_file) as data_file:
			data = json.load(data_file)

		id = []
		attendence = []
		for student in data['students']:
			id.append(str(student['id']))
			attendence.append(student['attendence'])
		graph = [
			dict(
				data =[
					dict(
						x=id,
						y=attendence,
						type = 'bar'
					),
				],
				layout=dict(
					title='Attendence'+selected_course,
					xaxis= dict(
						type='category'
	  				),
	  				yaxis=dict(
	  					tickformat=',d'
	  				)
				)
			)
		]

		conn = sqlite3.connect('student.db')
		cursor = conn.execute("select Name, Prof_name from courses where id = %s"%("\""+selected_course+"\""))
		course_name = prof_name = ""
		for row in cursor:
			course_name = row[0]
			prof_name = row[1]
		conn.close()

		ids = ['graph-{}'.format(i) for i, _ in enumerate(graph)]
		graphJSON = json.dumps(graph, cls=plotly.utils.PlotlyJSONEncoder)
		df = pd.read_csv(attendence_csv)
		data = pd.DataFrame()
		data['Id']=df['id']
		data['Name'] = df['name']
		df.pop('name')
		df.pop('id')
		df1 = df.pop('total_attendence')
		for x in df.columns:
			data[x]=df[x]
		data['total_attendence'] = df1
		return render_template('show_attendence.html',table=data.to_html(index=False),  title='attendence',  name=name,id=ids, graphJSON=graphJSON,course_name=course_name, prof_name=prof_name,logged_in=str(app.config['logged_in']))
	else :
		return render_template('home.html',name=name)

@app.route('/json/<found>', methods=['GET','POST'])
def json12(found=None):
    return json_response({'found_ids': found}, status_code=200)

if __name__ == '__main__':
	app.config['logged_in']=False
	app.run(debug=True,host="localhost",port="8080")
