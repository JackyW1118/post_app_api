from flask import Flask, render_template, redirect, url_for, jsonify, request
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import os
import json

app = Flask(__name__)
CORS(app)
app.config['JSON_SORT_KEYS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True

cred = credentials.Certificate()

firebase_admin.initialize_app(cred,{
    'databaseURL': 'https://postapp-48b9d.firebaseio.com/'
})
root = db.reference()

def getObject(post_type=None):
    if(post_type is None or post_type == "all"):
        return root.get()["post_app"]["post_app"]["post"]
    output = list()
    pk_list = json.loads(root.child("post_app").child("post_app").child("category").child(post_type).get())
    for key in pk_list:
        output.append(getPostObjWithPk(key))
    return output

def getPostObjWithPk(pk):
    return root.child("post_app").child("post_app").child("post").child(str(pk)).get()

def getAuthorObjWithUsername(username):
    return root.child("post_app").child("post_app").child("users").child(str(username)).get()

def upVotePostWithPk(pk,author):
    currentVal =  int(root.child("post_app").child("post_app").child("post").child(str(pk)).child("votes").get())
    newObj = getPostObjWithPk(pk)

    if not currentVal:
        newObj["votes"]="1"
    else:
        newObj["votes"] = str(currentVal+1)
    root.child("post_app").child("post_app").child("post").child(str(pk)).set(newObj)
    userobj = root.child("post_app").child("post_app").child("users").child(str(author)).get()
    voted = root.child("post_app").child("post_app").child("users").child(str(author)).child("votes").get()
    pk=int(pk)
    if(not voted):
        userobj["votes"] = str([pk])
    else:
        voted = json.loads(voted)
        voted.append(pk)
        userobj["votes"] = str(voted)
    root.child("post_app").child("post_app").child("users").child(str(author)).set(userobj)

def downVotePostWithPk(pk,author):
    currentVal =  int(root.child("post_app").child("post_app").child("post").child(str(pk)).child("votes").get())
    newObj = getPostObjWithPk(pk)

    if not currentVal:
        newObj["votes"]="-1"
    else:
        newObj["votes"] = str(currentVal-1)
    root.child("post_app").child("post_app").child("post").child(str(pk)).set(newObj)
    userobj = root.child("post_app").child("post_app").child("users").child(str(author)).get()
    voted = root.child("post_app").child("post_app").child("users").child(str(author)).child("votes").get()
    pk=int(pk)
    if (not voted):
        userobj["votes"] = str([pk])
    else:
        voted = json.loads(voted)
        voted.append(pk)
        userobj["votes"] = str(voted)
    root.child("post_app").child("post_app").child("users").child(str(author)).set(userobj)

def sortPostsByVote(descend,post_type):
    if descend ==0: #latest first
        return list(reversed(getObject(post_type)))
    elif descend == 1: #popular first
        descend = True
    elif descend == 2:#latest last
        return getObject(post_type)
    else: #popular last
        descend = False
    return sorted([x for x in getObject(post_type) if x is not None], key=lambda k: int(k['votes']),reverse=descend)

def ifVoted(pk,author):
    voted = root.child("post_app").child("post_app").child("users").child(str(author)).child("votes").get()
    if(not voted):
        return False
    print(type(voted))
    voted = json.loads(voted)
    return pk in voted

def getCategoryNames():
    return list(root.child("post_app").child("post_app").child("category").get().keys())

@app.route('/')
def home_page():
    data  = getObject()
    return render_template('home.html',post_obj=data ,categories=getCategoryNames())

@app.route('/all/<order>')
def allPosts(order=0):
    post_type = request.args.get('type')
    return jsonify(sortPostsByVote(int(order),post_type))

@app.route('/posts/<pk>')
def post_detail(pk=None):
    data = getPostObjWithPk(pk)
    return render_template('post_detail.html', post_obj=data)

@app.route('/posts/<pk>/upvote/<voter>')
def upvote_post(pk=None, voter = None):
    if(ifVoted(int(pk),voter)==False):
        upVotePostWithPk(pk,author=voter)
        return "true"
    return "false"

@app.route('/posts/<pk>/downvote/<voter>')
def downvote_post(pk=None, voter=None):
    if(ifVoted(int(pk),voter)==False):
        downVotePostWithPk(pk,author=voter)
        return "true"
    return "false"

@app.route('/author/<author>')
def user_posts(author=None):
    author=author.replace('"','')
    post_obj=[]
    for post_dict in getObject():
        if post_dict is not None and post_dict["author"].replace('"',"") == author:
            post_obj.append(post_dict)
    return render_template('user_posts.html',post_obj=post_obj,author=getAuthorObjWithUsername(author))

@app.route('/posts/<pk>/votes')
def getVoteWithPk(pk=None):
    return getPostObjWithPk(pk)["votes"]


if __name__ == '__main__':
    #testing func, to run server, go to upper directory and run wsgi.py
    #print(downVotePostWithPk(pk='5',author="jackyw118"))
    print(ifVoted(5,"jackyw118"))
