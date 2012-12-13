from webbattle import app
from models import Post, Battle, Comment, UserVote
from flask import render_template, flash, redirect, url_for, request, jsonify, Response, current_app
from flaskext import wtf
from flaskext.wtf import validators
from decorator import login_required
from google.appengine.api import users, mail
from google.appengine.ext import db
from datetime import datetime

class PostForm(wtf.Form):
    title = wtf.TextField('Title', validators=[validators.Required()])
    content = wtf.TextAreaField('Content', validators=[validators.Required()])

class IndexForm(wtf.Form):
	left = wtf.TextField('Left', validators=[validators.Required()])
	right = wtf.TextField('Right', validators=[validators.Required()])

class CommentForm(wtf.Form):
	comment = wtf.TextAreaField('Comment', validators=[validators.Length(max=140)])

@app.route('/posts')
def list_posts():
	posts = Post.all()
	return render_template('list_posts.html', posts=posts)

@app.route('/posts/new',methods = ['GET','POST'])
@login_required
def new_post():
	form = PostForm()
	if form.validate_on_submit():
		post = Post(title = form.title.data,
					content = form.content.data,
					author = users.get_current_user())
		post.put()
		flash('Post saved on database.')
		return redirect(url_for('list_posts'))
	return render_template('new_post.html', form=form)

def battle_key(left=None, right=None):
  	"""Constructs a Datastore key for a battle entity with left and right."""
  	return db.Key.from_path('Battle', left+right)

def comment_key(comment=None, author=None, when=None):
	"""constructs a Datastore key fr a comment entity with comment, author of the comment and the date of comment posted"""
	return db.Key.from_path('Comment', comment+author+when)

def send_emails(leftf=None,rightf=None,comment=""):
	battle = Battle.all().filter('left =',leftf).filter('right =',rightf).get()
	message = mail.EmailMessage(sender="hm1021@nyu.edu",
								subject="An update on Battle " + leftf + " vs " + rightf)
	for subscriber in battle.subscribers:
		message.to = subscriber
		message.body = comment + "\n by " + users.get_current_user().nickname()
		message.send()

@app.route('/battle/<leftf>/<rightf>',methods = ['GET','POST'])
def left_right(leftf,rightf):
	left = CommentForm()
	right = CommentForm()
	left_comments = Comment.all().ancestor(battle_key(leftf,rightf)).order('-votes').filter('side =','left')
	right_comments = Comment.all().ancestor(battle_key(leftf,rightf)).order('-votes').filter('side =','right')
	time = datetime.now()
	if request.form.has_key('leftb'):
		leftComment = Comment(key_name = request.form.get('comment')+users.get_current_user().email()+str(time),
							parent=battle_key(leftf,rightf),
							comment = request.form.get('comment'),
							author = users.get_current_user(),
							side = "left",
							when = time)
		leftComment.put()
		send_emails(leftf,rightf,request.form.get('comment'))
	elif request.form.has_key('rightb'):
		rightComment = Comment(key_name = request.form.get('comment')+users.get_current_user().email()+str(time),
							parent=battle_key(leftf,rightf),
							comment = request.form.get('comment'),
							author = users.get_current_user(),
							side = "right",
							when = time)
		rightComment.put()
		send_emails(leftf,rightf,request.form.get('comment'))
	return render_template('battle.html',left=left,right=right,leftf=leftf,rightf=rightf,lc=left_comments,rc=right_comments)

def check_for_user_vote(comment_key,vote):
	userVote = UserVote.all().ancestor(comment_key).filter('author =',users.get_current_user()).get()
	if not userVote:
		insert = UserVote(parent=comment_key,
						author=users.get_current_user(),
						vote=vote)
		insert.put()
		return True
	user_vote = userVote.vote
	if user_vote == vote:
		return False
	else:
		userVote.vote = user_vote + vote
		userVote.put()
		return True

@app.route('/battle/upvote/<leftf>/<rightf>',methods = ['GET','POST'])
def upvote_comment(leftf,rightf):
	comments = Comment.all().ancestor(battle_key(leftf,rightf)).filter('side =',request.form.get('side'))
	current_comment = comments.filter('comment =',request.form.get('comment')).filter('author =',users.User(request.form.get('author'))).filter('when =',datetime.strptime(request.form.get('when'),'%Y-%m-%d %H:%M:%S.%f')).get()
	if check_for_user_vote(comment_key(current_comment.comment,request.form.get('author'),request.form.get('when')),1):
		current_comment.votes = current_comment.votes + 1
		current_comment.put()
	votes = current_comment.votes
	return jsonify(votes=votes)

@app.route('/battle/downvote/<leftf>/<rightf>',methods = ['GET','POST'])
def downvote_comment(leftf,rightf):
	comments = Comment.all().ancestor(battle_key(leftf,rightf)).filter('side =',request.form.get('side'))
	current_comment = comments.filter('comment =',request.form.get('comment')).filter('author =',users.User(request.form.get('author'))).filter('when =',datetime.strptime(request.form.get('when'),'%Y-%m-%d %H:%M:%S.%f')).get()
	if check_for_user_vote(comment_key(current_comment.comment,request.form.get('author'),request.form.get('when')),-1):
		current_comment.votes = current_comment.votes - 1
		current_comment.put()
	votes = current_comment.votes
	return jsonify(votes=votes)

@app.route('/battle/subscribe/<leftf>/<rightf>',methods = ['GET','POST'])
def subscribe(leftf,rightf):
	battle = Battle.all().filter('left =',leftf).filter('right =',rightf).get()
	battle.subscribers.append(str(users.get_current_user().email()))
	battle.put()
	return Response(status=200)

@app.route('/battle/unsubscribe/<leftf>/<rightf>',methods = ['GET','POST'])
def unsubscribe(leftf,rightf):
	battle = Battle.all().filter('left =',leftf).filter('right =',rightf).get()
	battle.subscribers.remove(str(users.get_current_user().email()))
	battle.put()
	return Response(status=200)

@app.route('/upvote',methods = ['GET','POST'])
def upvote_battle():
	left = request.form.get('left')
	right = request.form.get('right')
	battle = Battle.all().filter('left =',left).filter('right =',right).get()
	battle.upvotes = battle.upvotes + 1
	battle.put()
	votes = battle.upvotes - battle.downvotes
	return jsonify(votes=votes)

@app.route('/downvote',methods = ['GET','POST'])
def downvote_battle():
	left = request.form.get('left')
	right = request.form.get('right')
	battle = Battle.all().filter('left =',left).filter('right =',right).get()
	battle.downvotes = battle.downvotes + 1
	battle.put()
	votes = battle.upvotes - battle.downvotes
	return jsonify(votes=votes)

@app.route('/',methods = ['GET','POST'])
@login_required
def add_battle():
	if request.form.has_key('left'):
		battle = Battle(key_name = request.form.get('left')+request.form.get('right'),
						left = request.form.get('left'),
						right = request.form.get('right'),
						author = users.get_current_user())
		for i in request.form.get('tags').split(','):
			if not i == "":
				battle.tags.append(i)
		battle.put()
		flash('The battle has been created.')
	battles = Battle.all()
	return render_template('new_index.html', battles=battles)

# @login_required
# def index():
# 	form = IndexForm()
# 	if form.validate_on_submit():
# 		battle = Battle(key_name = form.left.data+form.right.data,
# 						left = form.left.data,
# 						right = form.right.data,
# 						author = users.get_current_user())
# 		battle.put()
# 		flash('The battle has been created.')
# 	battles = Battle.all()
# 	return render_template('new_battle.html', form=form, battles=battles)
