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
from flask import Flask, request, render_template, send_file,jsonify
import fitz

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


global DOCS_DIR,INDEX_DIR
# 设置检索文件目录和数据库文件路径
DOCS_DIR = "/path/to/docs"
INDEX_DIR = "/path/to/index"

# 定义检索索引模式
schema = Schema(path=ID(stored=True), content=TEXT(stored=True))

# 检查索引目录是否存在，如果不存在则创建
if not os.path.exists(INDEX_DIR):
    os.makedirs(INDEX_DIR)

# 建立或打开检索索引
ix = index.create_in(INDEX_DIR, schema)
writer = ix.writer()

# 遍历检索文件目录，将所有pdf和word文件加入索引
for root, dirs, files in os.walk(DOCS_DIR):
    for file in files:
        content=''
        if file.endswith(".doc") or file.endswith(".docx") :
            path = os.path.join(root, file)
            doc = Document(path);
            for para in doc.paragraphs:
                content+=para.text+'\n'
            writer.add_document(path=path, content=content)
        elif file.endswith(".pdf"):
            path = os.path.join(root, file)
            with fitz.open(path) as doc:
                for page in doc.pages():
                   content += page.get_text()
            writer.add_document(path=path, content=content)
# 提交并关闭索引写入器
writer.commit()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST','GET'])
def select_folderName():
 FolderName = filedialog.askdirectory()  #获取文件夹
 print(FolderName)
 DOCS_DIR = FolderName
 return render_template("index.html")

@app.route("/test",methods=['POST','GET'])
def test():
 return render_template("index.html")

@app.route('/submit_result',methods=['GET','POST'])
def submit():
    if request.method=='POST':
        keywords=request.form['keywords']
    elif request.method=='GET':
        keywords=request.args.get('keywords')
    outcome=[]
    with ix.searcher() as searcher:
       query = QueryParser('content', ix.schema).parse(keywords)
       ##search(query, limit=None)
       results = searcher.search(query, limit=None)
       for res in results:
        print("```")
        print(res['path'])
        print("-------------------------------")
        search_lines(res['content'],keywords)
        print()
        outcome+=get_keywords_lines(res['content'],keywords)
       return render_template("index.html",outcome=outcome)


