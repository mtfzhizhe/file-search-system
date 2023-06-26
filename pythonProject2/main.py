import os
import whoosh.index as index
from whoosh.fields import *
from whoosh.qparser import QueryParser
from whoosh.query import *
import docx
from docx import Document
from flask import Flask, request, render_template, send_file
import fitz

def search_lines(content,keywords):
    word_position = content.find(keywords)
    tail = content.find('\n',word_position)
    head = content.rfind('\n',0,word_position)
    start = -1
    line = 1
    while(start!=head):
     start = content.find('\n',start+1)
     line+=1
    print(str(line)+" ",end="")
    print(content[head+1:tail])


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

# 创建一个检索器
with ix.searcher() as searcher:
    # 创建query对象，被用来搜索的
    # QueryParser(检索的字段名, 索引结构).parse(关键词)
    query = QueryParser('content', ix.schema).parse('generation')
    # 使用搜索对象的搜索方法来完成检索
    # search(query, limit=None)
    # limit限制搜索结果的条数，默认为10个，指定为None则显示所有
    results = searcher.search(query, limit=None)
    for res in results:
        print("```")
        print(res['path'])
        print("-------------------------------")
        search_lines(res['content'],'generation')
        print()



