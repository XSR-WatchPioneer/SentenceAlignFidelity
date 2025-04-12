import os
import re

from fuzzywuzzy import process

from LLM_API import LLM_model, ChooseLLM, MyLLMs
from LLM_tools import LLM_Stream_Response


def arrange_titles(md_file_path, model: LLM_model, replace=True):
    def replace_titles(no_number=False):
        # 读取markdown文件内容
        with open(md_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # 对于每个新标题，找到内容相似度最高的旧标题并替换
        for new_title in new_titles:
            old_title = process.extractOne(new_title, old_titles)[0]
            lines = [line.replace(old_title, new_title + '\n') if line == old_title else line for line in lines]

            # print(f"{old_title} ====> {new_title}")

        # 如果不需要保留标题的序号，去掉序号
        if no_number:
            titles = [line for line in lines if line.startswith('#')]
            for title in titles:
                # 用第一个空格分割字符串为前后两部分a和b
                prefix, content = title.split(' ', 1)
                # 对b做处理：若b的首个字符是数字，"."或者空格，则将其删除，直至b不以这三类字符开头为止
                content = content.lstrip('0123456789. ')
                new_title = prefix + ' ' + content
                # 替换标题
                lines = [line.replace(title, new_title) if line == title else line for line in lines]

        if replace:
            # 将修改后的内容写入原markdown文件
            with open(md_file_path, 'w', encoding='utf-8') as file:
                file.writelines(lines)
            print(f"标题已经成功替换，原markdown文件已经被覆盖。")
            return md_file_path
        else:
            # 将修改后的内容写入新的markdown文件
            new_md_file_path = os.path.splitext(md_file_path)[0] + '_调整标题.md'
            with open(new_md_file_path, 'w', encoding='utf-8') as file:
                file.writelines(lines)

            print(f"标题已经成功替换，新的markdown文件路径为：{new_md_file_path}")
            return new_md_file_path

    # 获取原文的所有标题
    with open(md_file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    old_titles = [line for line in lines if re.match(r"^(#{1,6})\s*(.*)", line)]
    # for old_title in old_titles:
    # print(old_title)

    # 循环生成直到有多个一级标题
    retry_count = 0
    max_retries = 3

    while retry_count < max_retries:
        # 调用LLM调整标题级别
        # new_titles = utils.simple_llm_api_process(
        #     content="\n".join(old_titles),
        #     api_key=model.api_key,
        #     url=model.base_url,
        #     model=model.model_name,
        #     prompt="""
        #             将以下Markdown标题重新调整级别，从1级算起，章节标题与文章标题同设为1级。
        #             注意：
        #             - 去掉标题中多余的空白，但不要改变标题内容
        #             - 如果标题有编号，保留编号不要删掉
        #             - 直接给出结果，不要输出多余内容
        #             """,
        #     print_result=False
        # )
        new_titles,token_usage = LLM_Stream_Response(
            model=model,
            prompt=f"""
请帮我整理以下混乱的Markdown标题层级结构，要求：
- 将整个文档的标题层级重新调整为从1级(#)开始的规范结构
- 文章主标题和章节标题都设为1级标题(即使用#)
- 子章节按层级依次使用##、###等
- 完全保留原有的标题编号（如果有）
- 保持原有的标题文本内容不变，仅调整#的数量
- 只输出整理后的Markdown内容，不要添加任何解释或说明
"""+"\n".join(old_titles),
        )
        new_titles = new_titles.split('\n')
        new_titles = [line for line in new_titles if re.match(r"^(#{1,6})\s*(.*)", line)]
        # 新老标题数量不一致则重试
        if len(new_titles) != len(old_titles):
            print("新标题数量与旧标题数量不一致，重新生成...")
            retry_count += 1
            continue
        # 计算一级标题数量
        level1_count = sum(1 for title in new_titles if title.startswith('# '))
        if level1_count > 1:
            break
        print("一级标题数量不足，重新生成...")
        retry_count += 1

    if retry_count >= max_retries:
        raise RuntimeError("重试3次后仍未生成合适的标题结构，程序终止")

    replace_titles()

if __name__ == '__main__':
    #测试
    md_file_path = r"D:\Obsidian Vault\云容器\其余\2020_EN_一种微服务架构中检测工件异常的方法_md\2020_EN_一种微服务架构中检测工件异常的方法.md"
    selected_llm = ChooseLLM(MyLLMs)
    arrange_titles(md_file_path, selected_llm, replace=False)
