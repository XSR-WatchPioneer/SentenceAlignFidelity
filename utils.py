import os
import re
import tkinter as tk
from tkinter import filedialog

from openai import OpenAI


# 获取用户输入的markdown文件路径
def get_md_file_path(tip="请输入markdown文件路径："):
    while True:
        md_file_path = input(tip)
        # 若文件路径被""包裹，去掉""
        if (md_file_path.startswith('"') and md_file_path.endswith('"')):
            md_file_path = md_file_path[1:-1]
        # 检查文件是否存在
        if os.path.exists(md_file_path):
            break
        else:
            print("文件不存在，请重新输入。")
    return md_file_path

# 简单调用LLM的API进行处理
def simple_llm_api_process(content, api_key, url, model, prompt, system_prompt=None, print_result=True):
    client = OpenAI(api_key=api_key,base_url= url)
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt if system_prompt else "You are a helpful assistant."},
            {"role": "user", "content": prompt +'\n'+ content},
        ],
        stream=True,
    )
    content = ""
    for chunk in completion:
        if chunk.choices:
            delta = chunk.choices[0].delta
            if hasattr(delta, 'content') and delta.content:
                content += chunk.choices[0].delta.content
                if print_result:
                    print(delta.content, end='', flush=True)
    return content




# 拆分Markdown成块
def split_markdown_into_blocks(lines,skip_empty_line=True):
    # 定义Markdown各个部分的正则表达式
    patterns = {
        "header": r"^(#{1,6})\s*(.*)",  # 匹配标题，#、##、### 等
        "standard_link": r"^\s*\!\[(.*?)\]\((.*?)\)\s*$", # 匹配wiki型链接![[]]
        "wiki_link": r"^\s*\!\[\[(.*?)\]\]\s*$",  # 匹配标准链接 ![alt text](url)
        "code_block_start": r"^```",  # 匹配代码块开始 ```
        "code_block_end": r"^```",  # 匹配代码块结束 ```
        "formula_block_start": r"^\$\$\s*$",  # 匹配公式块开始 $$
        "formula_block_end": r"^\$\$\s*$",  # 匹配公式块结束 $$
        "single_line_formula": r"^\$\$.*\$\$$",  # 匹配单行公式 $formula$
        "inline_formula": r"^\s*\$\s*.*\s*\$\s*$",
        "yaml_start": r"^---\s*$",  # 匹配YAML头开始 ---
        "yaml_end": r"^---\s*$",  # 匹配YAML头结束 ---
        "table": r"^<table>.*</table>$",  # 匹配单行表格 <table>...</table>
        "markdown_table_row": r"^\s*\|.*\|\s*$",  # 匹配Markdown表格行
        "markdown_table_separator": r"^\s*\|[\s\-\|:]*\|\s*$",  # 匹配表格分隔符行
    }

    blocks = []

    in_code_block = False
    in_formula_block = False
    in_yaml_block = False
    in_markdown_table = False
    current_code_block = []
    current_formula_block = []
    current_yaml_block = []
    current_markdown_table = []

    for line in lines:
        # 处理代码块
        if in_code_block:
            current_code_block.append(line)
            if re.match(patterns["code_block_end"], line):
                # 代码块结束
                blocks.append(("code_block", "".join(current_code_block)))
                in_code_block = False
                current_code_block = []
            continue

        # 处理公式块
        if in_formula_block:
            current_formula_block.append(line)
            if re.match(patterns["formula_block_end"], line):
                # 公式块结束
                blocks.append(("formula", "".join(current_formula_block)))
                in_formula_block = False
                current_formula_block = []
            continue

        # 处理YAML头
        if in_yaml_block:
            current_yaml_block.append(line)
            if re.match(patterns["yaml_end"], line):
                # YAML头结束
                blocks.append(("yaml", "".join(current_yaml_block)))
                in_yaml_block = False
                current_yaml_block = []
            continue

        # 处理Markdown表格
        if in_markdown_table:
            if re.match(patterns["markdown_table_row"], line) or re.match(patterns["markdown_table_separator"], line):
                current_markdown_table.append(line)
                continue
            else:
                # 表格结束
                if current_markdown_table:
                    blocks.append(("markdown_table", "".join(current_markdown_table)))
                    in_markdown_table = False
                    current_markdown_table = []
                # 不要continue，因为当前行需要继续处理

        # 匹配代码块开始
        if re.match(patterns["code_block_start"], line):
            in_code_block = True
            current_code_block.append(line)
            continue

        # 匹配公式块开始
        if re.match(patterns["formula_block_start"], line):
            in_formula_block = True
            current_formula_block.append(line)
            continue

        # 匹配YAML头开始
        if re.match(patterns["yaml_start"], line):
            in_yaml_block = True
            current_yaml_block.append(line)
            continue

        # 匹配Markdown表格
        if re.match(patterns["markdown_table_row"], line) and not in_markdown_table:
            in_markdown_table = True
            current_markdown_table.append(line)
            continue

        # 匹配标题
        if re.match(patterns["header"], line):
            # blocks.append(("header", re.match(patterns["header"], line).groups()))
            blocks.append(("header", line))
        # 匹配链接
        elif re.findall(patterns["standard_link"], line):
            # images = re.findall(patterns["image"], line)
            # for alt_text, url in images:
            #     blocks.append(("link", alt_text, url))
            blocks.append(("link", line))
        elif re.findall(patterns["wiki_link"], line):
            # images = re.findall(patterns["image"], line)
            # for alt_text, url in images:
            #     blocks.append(("link", alt_text, url))
            blocks.append(("link", line))
        # 匹配单行公式
        elif re.match(patterns["single_line_formula"], line):
            blocks.append(("formula", line))
        # 匹配单$包裹的单行公式
        elif re.search(patterns["inline_formula"], line):
            blocks.append(("formula", line))
        # 匹配表格
        elif re.match(patterns["table"], line):
            blocks.append(("table", line))
        # 跳过空行
        elif not line.strip():
            if skip_empty_line:
                continue
            else:
                blocks.append(("empty_line", line))

        # 匹配段落
        else:
            blocks.append(("paragraph", line))

    # 处理文件末尾可能的未闭合表格
    if in_markdown_table and current_markdown_table:
        blocks.append(("markdown_table", "".join(current_markdown_table)))

    return blocks


def determine_heading_level(title):
    """
    判断给定Markdown块的标题等级。
    返回:
        int: 标题等级，如果不是标题则返回0。
    """
    title = title.strip()
    # 计算从左到右的 # 数量，直到遇到第一个非 # 字符
    for i, char in enumerate(title):
        if char != '#':
            return i
    return 0


# 检查Markdown块是否一致
def check_blocks_consistency(en_blocks, ch_blocks ,en_lines, ch_lines):
    # 跳过yaml块
    en_blocks = [block for block in en_blocks if block[0] != "yaml"]
    ch_blocks = [block for block in ch_blocks if block[0] != "yaml"]
    # 打印块数
    print(f"英文块数：{len(en_blocks)}")
    print(f"中文块数：{len(ch_blocks)}")
    # 比较块类型
    for i, (en_block, ch_block) in enumerate(zip(en_blocks, ch_blocks)):
        if en_block[0] != ch_block[0]:
            print(f"第 {i+1} 个块类型不一致")
            #查找块的开头在原文中的行号
            en_block_start_line = en_lines.index(en_block[1])+1
            ch_block_start_line = ch_lines.index(ch_block[1])+1
            print(f"===>英文行号：{en_block_start_line}")
            print(f"===>中文行号：{ch_block_start_line}")
            # 打印块的类型和内容
            print(f"英文块类型:{en_block[0]}")
            print(f"{en_block[1]}")
            print(f"中文块类型:{ch_block[0]}")
            print(f"{ch_block[1]}")
            return False

    # 比较块数
    if len(en_blocks) != len(ch_blocks):
        print(f"块数不一致: {len(en_blocks)} vs {len(ch_blocks)}")
        return False

    return True


# 对md块计算单词
def count_words(block):
    return len(re.findall(r'\w+', block[1]))


def merge_markdown_blocks(blocks, max_words, by_top_section=False, try_title=True):

    # 统计指定索引之间的单词数
    def count_words_between(blocks, start, end):
        return sum(count_words(block) for block in blocks[start:end])

    # 合并指定索引之间的块
    def merge_blocks(blocks, start, end):
        return '\n\n'.join(block[1] for block in blocks[start:end])  # 强化换行

    # 记录所有标题块的索引位置
    header_indices = [i for i, (block_type, _) in enumerate(blocks) if block_type == 'header']
    if by_top_section:# 仅提取一级标题
        header_indices = [i for i, (block_type, block_content) in enumerate(blocks) if block_type == 'header' and determine_heading_level(block_content)==1]
    current_index = 0
    result = []

    while current_index < len(blocks):
        # 从最近的标题块开始计算单词数
        # 记录所有大于当前块的标题块索引
        possible_end_index = current_index
        if try_title:
            next_header_indices = [header_index for header_index in header_indices if header_index > current_index]

            # 尝试合并当前块和最近标题块之间的块
            for next_header_index in next_header_indices:
                if count_words_between(blocks, current_index, next_header_index) > max_words:
                    break
                else:
                    possible_end_index = next_header_index

        # 如果没有找到合适的标题块，直接合并至最大长度
        if possible_end_index == current_index:
            end_index = current_index
            while end_index < len(blocks) and count_words_between(blocks, current_index, end_index) < max_words:
                end_index += 1
            result.append(merge_blocks(blocks, current_index, end_index+1))
            current_index = end_index+1
        else:
            result.append(merge_blocks(blocks, current_index, possible_end_index))
            current_index = possible_end_index
    return result


# 按照一级标题分块
def merge_by_top_section(blocks):
    result = []
    current_section = []
    for block in blocks:
        if (block[0] == 'header' and determine_heading_level(block[1]) == 1):
            if current_section:
                result.append(current_section)
            current_section = [block]
        else:
            current_section.append(block)
    if current_section:
        result.append(current_section)
    return result



def select_pdf():
    # 打开文件对话框选择PDF文件
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    pdf_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    return pdf_path


def select_pdf_files():
    """
    打开文件选择对话框，支持选择多个PDF文件
    Returns:
        list: 选中的PDF文件路径列表，如果用户未选择则返回空列表
    """
    root = tk.Tk()
    root.withdraw()
    pdf_paths = filedialog.askopenfilenames(
        title="选择一个或多个PDF文件",
        filetypes=[("PDF files", "*.pdf")]
    )
    return list(pdf_paths)  # 将返回的tuple转换为list

def select_md():
    root = tk.Tk()
    root.withdraw()
    md_path = filedialog.askopenfilename(filetypes=[("Markdown files", "*.md")])
    return md_path if md_path else ""


def select_md_files():
    """
    打开文件选择对话框，支持选择多个markdown文件
    Returns:
        list: 选中的markdown文件路径列表，如果用户未选择则返回空列表
    """
    root = tk.Tk()
    root.withdraw()
    md_paths = filedialog.askopenfilenames(
        title="选择一个或多个Markdown文件",
        filetypes=[("Markdown files", "*.md")]
    )
    return list(md_paths)  # 将返回的tuple转换为list

def select_md_or_pdf_files():
    """
    选择一个或多个Markdown或PDF文件
    返回文件路径列表
    """
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    file_paths = filedialog.askopenfilenames(
        title="选择Markdown或PDF文件",
        filetypes=[("Markdown/PDF文件", "*.md *.pdf"), ("Markdown文件", "*.md"), ("PDF文件", "*.pdf"), ("所有文件", "*.*")]
    )

    if not file_paths:
        print("未选择任何文件")
        return []

    return list(file_paths)

def get_markdown_titles(md_file_path):
    with open(md_file_path, 'r', encoding='utf-8') as file:
        content = file.readlines()
    titles = []
    for line in content:
        if re.match(r"^(#{1,6})\s*(.*)", line):
            titles.append(line)
    return titles


# 执行markdown中的文本替换功能
def replace_all(file_path, old_str, new_str):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    content = content.replace(old_str, new_str)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    print(f"已将所有'{old_str}'替换为'{new_str}'")


def clean_filename(filename):
    """清理文件名，去除Windows不支持的字符"""
    # Windows文件名中不允许出现的字符: \ / : * ? " < > |
    invalid_chars = r'[\\/:*?"<>|]'
    # 将非法字符替换为下划线
    cleaned_name = re.sub(invalid_chars, '_', filename)
    # 去除首尾空格
    cleaned_name = cleaned_name.strip()
    # 如果文件名为空，返回默认名称
    return cleaned_name if cleaned_name else 'untitled'

if __name__ == '__main__':
    # 测试select_md_files
    print(
        select_md_files()
    )

    # 测试split_markdown_into_blocks
    # with open(r"E:\Study\常用脚本\Markdown处理\测试Markdown\test_各种MarkdownBlock识别.md", 'r', encoding='utf-8') as file:
    #     whole_text = file.readlines()
    # blocks = split_markdown_into_blocks(whole_text)
    # for block in blocks:
    #     print(block)
