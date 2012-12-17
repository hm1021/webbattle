from webbattle import app
from models import Battle, Comment, UserVote
from flask import render_template, flash, redirect, url_for, request, jsonify, Response, current_app
from flaskext import wtf
from flaskext.wtf import validators
from decorator import login_required
from google.appengine.api import users, mail, images
from google.appengine.ext import db, blobstore
from datetime import datetime
from werkzeug import parse_options_header

@app.route('/battle/subscribe/<key>',methods = ['GET','POST'])
@login_required
def subscribe(key):
	battle = Battle.get(key)
	if not battle.subscribers.__contains__(users.get_current_user().email()):
		battle.subscribers.append(str(users.get_current_user().email()))
		battle.put()
	return Response(status=200)

@app.route('/battle/unsubscribe/<key>',methods = ['GET','POST'])
@login_required
def unsubscribe(key):
	battle = Battle.get(key)
	battle.subscribers.remove(str(users.get_current_user().email()))
	battle.put()
	return Response(status=200)

def check_for_user_vote_battle(battle,vote):
	uservote = UserVote.all().ancestor(battle).filter('author =',users.get_current_user()).get()
	if not uservote:
		new_uservote = UserVote(parent=battle.key(), author=users.get_current_user(),vote=vote)
		new_uservote.put()
		return True
	old_uservote = uservote.vote
	if old_uservote == vote:
		return False
	else:
		uservote.vote = old_uservote + vote
		uservote.put()
		return True

@app.route('/battle/vote/<battle_key>/<up_or_down>', methods = ['GET','POST'])
@login_required
def vote_battle(battle_key,up_or_down):
	vote = 1 if up_or_down == "up" else -1
	battle = Battle.get(battle_key)
	if check_for_user_vote_battle(battle, vote):
		battle.votes = battle.votes + vote
		battle.put()
	votes = battle.votes
	return jsonify(votes=votes)


def check_for_user_vote(comment,vote):
	uservote = UserVote.all().ancestor(comment).filter('author =',users.get_current_user()).get()
	if not uservote:
		new_uservote = UserVote(parent=comment.key(), author=users.get_current_user(),vote=vote)
		new_uservote.put()
		return True
	old_uservote = uservote.vote
	if old_uservote == vote:
		return False
	else:
		uservote.vote = old_uservote + vote
		uservote.put()
		return True

@app.route('/comment/vote/<comment_key>/<up_or_down>', methods = ['GET','POST'])
@login_required
def vote_comment(comment_key,up_or_down):
	vote = 1 if up_or_down == "up" else -1
	comment = Comment.get(comment_key)
	if check_for_user_vote(comment, vote):
		comment.votes = comment.votes + vote
		comment.put()
	votes = comment.votes
	return jsonify(votes=votes)


def send_emails(key,comment):
	battle = Battle.get(key)
	message = mail.EmailMessage(sender="hm1021@nyu.edu",
								subject="An update on Battle " + battle.left + " vs " + battle.right)
	for subscriber in battle.subscribers:
		message.to = subscriber
		message.body = comment + "\n by " + users.get_current_user().nickname()
		message.send()


@app.route('/post_comment/<key>',methods=['GET','POST'])
@login_required
def post_comment(key):
	battle = Battle.get(key)
	now = datetime.now()
	if request.form.has_key('leftbox'):
		comment = request.form.get('leftbox')
		left_comment = Comment(parent=battle, comment=comment, author=users.get_current_user(), side="left", when=now)
		if request.files['left_image']:
			image_file = request.files['left_image']
			headers = image_file.headers['Content-Type']
			blob_key = parse_options_header(headers)[1]['blob-key']
			left_comment.blob_key = blob_key
			left_comment.image_url = images.get_serving_url(blob_key)
		left_comment.put()
		send_emails(key, comment)
	elif request.form.has_key('rightbox'):
		comment = request.form.get('rightbox')
		right_comment = Comment(parent=battle, comment=comment, author=users.get_current_user(), side="right", when=now)
		if request.files['right_image']:
			image_file = request.files['right_image']
			headers = image_file.headers['Content-Type']
			blob_key = parse_options_header(headers)[1]['blob-key']
			right_comment.blob_key = blob_key
			right_comment.image_url = images.get_serving_url(blob_key)
		right_comment.put()
		send_emails(key, comment)
	return left_right(key)

@login_required
@app.route('/battles/<key>',methods = ['GET','POST'])
def left_right(key):
	upload_url = blobstore.create_upload_url('/post_comment/'+key)
	battle = Battle.get(key)
	left_comments = Comment.all().ancestor(battle).order('-votes').filter('side =','left')
	right_comments = Comment.all().ancestor(battle).order('-votes').filter('side =','right')
	if battle.expirationDate and battle.expirationDate < datetime.now():
			return render_template('results.html',battle=battle,leftf=battle.left,rightf=battle.right,lc=left_comments,rc=right_comments)
	return render_template('battle.html',battle=battle,key=key,
		leftf=battle.left,rightf=battle.right,
		lc=left_comments,rc=right_comments,upload_url=upload_url,current_user=users.get_current_user().email())

@login_required
@app.route('/battles/tags/<tag>',methods=['GET','POST'])
def search_tag(tag):
	battle_with_tags = []
	battles = Battle.all()
	for battle in battles:
		for each_tag in battle.tags:
			if each_tag.lower() == tag.lower():
				battle_with_tags.append(battle)
	return render_template('all_battles.html',battles=battle_with_tags,title="Battles with tag " + tag,current_user=users.get_current_user().email()) 

@login_required
@app.route('/battles',methods=['GET','POST'])
def all_battles():
	battles = Battle.all()
	return render_template('all_battles.html',battles=battles,title="Existing Battles",current_user=users.get_current_user().email())

@login_required
@app.route('/battles/remove/<key>',methods=['GET','POST'])
def remove_battle(key):
	battle = Battle.get(key)
	if battle.author != users.get_current_user():
		return messages("You cannot delete this battle as you are not its owner")
	db.delete(battle)
	return redirect('/yourbattles')

@login_required
@app.route('/battles/edit/<key>',methods=['GET','POST'])
def edit_battle(key):
	battle = Battle.get(key)
	if battle.author != users.get_current_user():
		return messages("You cannot edit this battle as you are not its owner")

	left = request.form.get('left')
	right = request.form.get('right')
	date = request.form.get('date')
	tags = ""

	if battle.tags:
		for t in battle.tags:
			tags = tags + t + ','
	
	if request.method == 'POST':
		if check_existing_battle(left,right,battle):
			return Response(status=400)
		if date != 'None':
			battle.expirationDate = datetime.strptime(date,"%m/%d/%Y")
		battle.left = left
		battle.right = right
		form_tags = []
		for t in request.form.get('tags').split(','):
			form_tags.append(t.strip())
		battle.tags = []
		for tag in form_tags:
			if not tag == '':
				battle.tags.append(tag)
		battle.put()
		return Response(status=200)
	return render_template('edit_battle.html',battle=battle,tags=tags,date=battle.expirationDate.strftime("%m/%d/%Y"))

@login_required
@app.route('/messsages/<string>')
def messages(string):
	return render_template('messages.html',message=string)

@login_required
@app.route('/comment/remove/<key>/<battlekey>',methods=['GET','POST'])
def remove_comment(key,battlekey):
	comment = Comment.get(key)
	if comment.author != users.get_current_user():
		return redirect('/battles/'+battlekey)
	db.delete(comment)
	return redirect('/battles/'+battlekey)

def check_existing_battle(left,right,battle=None):
	existing_battles = Battle.all()
	for existing in existing_battles:
		if (existing.left.lower() == left.lower() and existing.right.lower() == right.lower()) or (existing.right.lower() == left.lower() and existing.left.lower() == right.lower()):
			if not battle:
				return True
			elif battle.key() != existing.key():
				return True
	return False

@app.route('/addbattle',methods=['GET','POST'])
@login_required
def add_a_battle():
	left = request.form.get('left')
	right = request.form.get('right')
	if check_existing_battle(left,right):
		return Response(status=400)
	battle = Battle(left=left,
					right=right,
					author = users.get_current_user())
	for tag in request.form.get('tags').split(','):
		if not tag.strip() == '' and not contains(battle,tag.strip()):
			battle.tags.append(tag.strip())
	if request.form.get('date') != '':
		battle.expirationDate = datetime.strptime(request.form.get('date'),"%m/%d/%Y")
	battle.put()
	return jsonify(key=str(battle.key()),left=left,right=right)

def contains(battle,tag):
	for t in battle.tags:
		if t.lower() == tag.lower():
			return True
		else:
			return False

@app.route('/logout')
def logout():
	return redirect(users.create_logout_url("/"))

@login_required
@app.route('/yourbattles')
def yourbattles():
	battles = Battle.all().filter('author =',users.get_current_user())
	return render_template('all_battles.html',battles=battles,title="Your Battles",current_user=users.get_current_user().email())

@app.route('/',methods = ['GET','POST'])
@login_required
def index():
	count = Battle.all().count()
	recent_battles = Battle.all().order('-when').order('-votes').fetch(5)
	return render_template('new_index.html', count=count, recent_battles=recent_battles)
