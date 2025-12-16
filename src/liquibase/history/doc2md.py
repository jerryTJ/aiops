from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph
import re

def table_to_markdown(table):
    """ 将 Word 表格转换为 Markdown 格式 """
    data = [[cell.text.strip() for cell in row.cells] for row in table.rows]
    if not data:
        return ""
    
    header = "| " + " | ".join(data[0]) + " |"
    separator = "| " + " | ".join(["---"] * len(data[0])) + " |"
    rows = "\n".join("| " + " | ".join(row) + " |" for row in data[1:])
    
    return f"{header}\n{separator}\n{rows}"

def get_paragraph_style(paragraph):
    """ 解析段落样式，识别标题、无序列表、有序列表 """
    style = paragraph.style.name.lower()
    text = paragraph.text.strip()

    # 识别标题（Heading 1、Heading 2）
    if "heading" in style:
        level = int(style.replace("heading ", ""))
        return f"{'#' * level} {text}"
    
    # 识别无序列表（• - –）
    if text.startswith(("•", "-", "–")):
        return f"- {text.lstrip('•-– ')}"
    
    # 识别有序列表（1. 2. 3. 或 ①②③）
    if re.match(r"^\d+\.", text):  # 匹配 "1. xxx"
        return f"1. {text}"
    
    if re.match(r"^[①②③④⑤⑥⑦⑧⑨⑩]", text):  # 匹配 "① xxx"
        return f"1. {text}"
    
    return text  # 普通段落

def docx_to_markdown(doc_path):
    """ 解析 Word 文档并转换为 Markdown 格式 """
    doc = Document(doc_path)
    markdown_output = []
    # 遍历文档元素
    for element in doc.element.body:
        if isinstance(element, CT_P):  # 处理段落
            para = Paragraph(element, doc)
            text = get_paragraph_style(para)
            if text:
                markdown_output.append(text)
        elif isinstance(element, CT_Tbl):  # 处理表格
            table = Table(element, doc)
            markdown_output.append(table_to_markdown(table))
    
    return "\n\n".join(markdown_output)


