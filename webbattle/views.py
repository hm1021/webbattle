from webbattle import app
from models import Post, Battle, Comment, UserVote
from flask import render_template, flash, redirect, url_for, request, jsonify, Response, current_app
from flaskext import wtf
from flaskext.wtf import validators
from decorator import login_required
from google.appengine.api import users, mail
from google.appengine.ext import db
from datetime import datetime

@app.route('/battle/subscribe/<key>',methods = ['GET','POST'])
def subscribe(key):
	battle = Battle.get(key)
	battle.subscribers.append(str(users.get_current_user().email()))
	battle.put()
	return Response(status=200)

@app.route('/battle/unsubscribe/<key>',methods = ['GET','POST'])
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
def vote_battle(battle_key,up_or_down):
	vote = 1 if up_or_down == "up" else -1
	battle = Battle.get(battle_key)
	if check_for_user_vote_battle(battle, vote):
		battle.votes = battle.votes + vote
		battle.put()
	votes = battle.votes
	return jsonify(votes=votes)
	# battle = Battle.get(battle_key)
	# if up_or_down == "up":
	# 	battle.votes = battle.votes + 1
	# else:
	# 	battle.votes = battle.votes - 1
	# battle.put()
	# votes = battle.votes
	# return jsonify(votes=votes)


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

@app.route('/post_comment/<key>',methods=['POST'])
def post_comment(key):
	battle = Battle.get(key)
	now = datetime.now()
	if request.form.has_key('leftbox'):
		comment = request.form.get('leftbox')
		left_comment = Comment(parent=battle, comment=comment, author=users.get_current_user(), side="left", when=now)
		left_comment.put()
		send_emails(key, comment)
	elif request.form.has_key('rightbox'):
		comment = request.form.get('rightbox')
		right_comment = Comment(parent=battle, comment=comment, author=users.get_current_user(), side="right", when=now)
		right_comment.put()
		send_emails(key, comment)
	return redirect('/battles/'+key)

@app.route('/battles/<key>',methods = ['GET','POST'])
def left_right(key):
	battle = Battle.get(key)
	left_comments = Comment.all().ancestor(battle).order('-votes').filter('side =','left')
	right_comments = Comment.all().ancestor(battle).order('-votes').filter('side =','right')
	return render_template('battle.html',key=key,
		leftf=battle.left,rightf=battle.right,
		lc=left_comments,rc=right_comments)

@app.route('/battles')
def all_battles():
	battles = Battle.all()
	return render_template('all_battles.html',battles=battles)

@app.route('/addbattle',methods=['GET','POST'])
def add_a_battle():
	left = request.form.get('left')
	right = request.form.get('right')
	battle = Battle(left=left, right=right, author = users.get_current_user())
	for tag in request.form.get('tags').split(','):
		if not tag == '':
			battle.tags.append(tag)
	battle.put()
	return jsonify(key=str(battle.key()),left=left,right=right)

@app.route('/',methods = ['GET','POST'])
@login_required
def index():
	recent_battles = Battle.all().order('-when').order('-votes').fetch(5)
	return render_template('new_index.html', recent_battles=recent_battles)
