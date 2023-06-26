import os
import whoosh.index as index
from whoosh.fields import *
from whoosh.qparser import QueryParser
from whoosh.query import *
import docx
from docx import Document
from flask import Flask, request, render_template, send_file
import fitz


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
searcher = ix.searcher()
searcher_str = "APPLE"
results = searcher.find("content",searcher_str)
print(results)
searcher.close()


