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
from flask import Flask, request, render_template, send_from_directory, session, redirect, url_for
import fitz
from jieba.analyse import ChineseAnalyzer
import random
import string
import psutil
import re

def get_disk_info():
    partitions = psutil.disk_partitions()
    disks = []
    for partition in partitions:
        if partition.fstype:
            disks.append({
                'mountpoint': partition.mountpoint,
                'device': partition.device
            })
    return disks

def generate_random_string(length):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for _ in range(length))

def get_directories(path):
    directories = []
    for entry in os.scandir(path):
        if entry.is_dir():
            directories.append(entry.name)
    return directories

def get_keywords_lines(content, keywords):
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
INDEX_DIR = "/path/to/index"

# 定义检索索引模式
schema = Schema(path=ID(stored=True), content=TEXT(stored=True,analyzer=ChineseAnalyzer()))

# 检查索引目录是否存在，如果不存在则创建
if not os.path.exists(INDEX_DIR):
    os.makedirs(INDEX_DIR)

# 建立或打开检索索引
ix = index.create_in(INDEX_DIR, schema)
app = Flask(__name__)
app.secret_key = generate_random_string(6)

@app.route('/', methods=['GET'])
def index_init():
    current_path = session.get('current_path', '/')
    directory = request.args.get('directory', '')
    disk = request.args.get('disk', '')

    if disk:
        current_path = disk

    if directory:
        if current_path != '/':
            current_path = os.path.join(current_path, directory)
        else:
            current_path = '/' + directory

    directories = get_directories(current_path)
    final_path = os.path.dirname(current_path) if current_path != '/' else '/'

    session['current_path'] = current_path  # 更新会话中的 current_path 变量

    disks = get_disk_info()

    return render_template('index.html', current_path=current_path, directories=directories, final_path=final_path, disks=disks)

@app.route("/upload",methods=['POST','GET'])
def upload():
    folder_path = session.get('current_path')
    create_index(str(folder_path))
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

@app.route('/reset', methods=['GET'])
def reset():
    session.pop('current_path', None)  # 重置会话中的 current_path 变量
    return render_template('index.html', current_path='/', directories=[], final_path='')

if __name__ == "__main__":
 app.run(host='127.0.0.1', port=8080,debug=True)

