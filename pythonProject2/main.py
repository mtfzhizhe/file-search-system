import os
from pprint import pprint
import eel
import whoosh.index as index
from whoosh.fields import *
from whoosh.qparser import QueryParser
from whoosh.query import *
import docx
from docx import Document
import tkinter as tk
from tkinter import filedialog
from flask import Flask, request, render_template, send_from_directory,session, redirect, url_for
import fitz
from jieba.analyse import ChineseAnalyzer
import json


def search_lines(content,keywords):
    search_position=0
    word_position = content.find(keywords, search_position)
    while(word_position!=-1):
     tail = content.find('\n',word_position)
     head = content.rfind('\n',0,word_position)
     start = -1
     line = 1
     while(start!=head):
      start = content.find('\n',start+1)
      line+=1
     print(str(line)+" ",end="")
     print(content[head+1:tail])
     search_position=tail
     word_position = content.find(keywords, search_position)

def get_keywords_lines(content,keywords):
    outcome=[]
    search_position=0
    word_position = content.find(keywords, search_position)
    while(word_position!=-1):
     tail = content.find('\n',word_position)
     head = content.rfind('\n',0,word_position)
     start = -1
     line = 1
     while(start!=head):
      start = content.find('\n',start+1)
      line+=1
     outcome.append(str(line)+" "+content[head+1:tail+1])
     search_position=tail
     word_position = content.find(keywords, search_position)
    return outcome
def create_index(folder_path):
    DOCS_DIR = folder_path
    writer = ix.writer()
    for root, dirs, files in os.walk(DOCS_DIR):
        for file in files:
            content = ''
            if file.endswith(".doc") or file.endswith(".docx"):
                path = os.path.join(root, file)
                doc = Document(path);
                for para in doc.paragraphs:
                    content += para.text + '\n'
                writer.add_document(path=path, content=content)
            elif file.endswith(".pdf"):
                path = os.path.join(root, file)
                with fitz.open(path) as doc:
                    for page in doc.pages():
                        content += page.get_text()
                writer.add_document(path=path, content=content)
    writer.commit()
# 设置检索文件目录和数据库文件路径
DOCS_DIR = "/path/to/docs"
INDEX_DIR = "/path/to/index"

# 定义检索索引模式
schema = Schema(path=ID(stored=True), content=TEXT(stored=True,analyzer=ChineseAnalyzer()))

# 检查索引目录是否存在，如果不存在则创建
if not os.path.exists(INDEX_DIR):
     os.makedirs(INDEX_DIR)

# 建立或打开检索索引
ix = index.create_in(INDEX_DIR, schema)
app = Flask(__name__)
app.secret_key = '123456'


@app.route('/')
def index_init():
    return render_template('index.html')

@app.route("/test",methods=['POST','GET'])
def test():
 return render_template("index.html")

@app.route("/upload",methods=['POST','GET'])
def upload():
    folder_path = request.form.get('folder_path')
    create_index(folder_path)
    session['folder_path']=folder_path
    return redirect(url_for('result_page'))


@app.route('/result_page')
def result_page():
    folder_path = session.get('folder_path')
    return render_template('index.html', folder_path=folder_path)

@app.route('/submit_result',methods=['GET','POST'])
def submit():
    if request.method=='POST':
        keywords=request.form['keywords']
    elif request.method=='GET':
        keywords=request.args.get('keywords')
    outcome={}
    with ix.searcher() as searcher:
       query = QueryParser('content', ix.schema).parse(keywords)
       ##search(query, limit=None)
       results = searcher.search(query, limit=None)
       for res in results:
        outcome[res['path']]=get_keywords_lines(res['content'],keywords)
       folder_path = session.get('folder_path')
       return render_template("index.html",outcome=outcome,user_input=keywords,folder_path=folder_path)

if __name__ == "__main__":
 app.run(host='127.0.0.1', port=8080,debug=True)
