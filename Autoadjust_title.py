import os
import re

from fuzzywuzzy import process

import utils
from LLM_API import LLM_model


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
        new_titles = utils.simple_llm_api_process(
            content="\n".join(old_titles),
            api_key=model.api_key,
            url=model.base_url,
            model=model.model_name,
            prompt="""
                    将以下Markdown标题重新调整级别，从1级算起，章节标题与文章标题同设为1级。
                    注意：
                    - 去掉标题中多余的空白，但不要改变标题内容
                    - 如果标题有编号，保留编号不要删掉
                    - 直接给出结果，不要输出多余内容
                    """,
            print_result=False
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


def arrange_titles_interactive(md_file_path, model: LLM_model, replace=True):
    def replace_titles(no_number=False):
        # 读取markdown文件内容
        with open(md_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # 统计
        print(f"旧标题数量：{len(old_titles)}")
        print(f"新标题数量：{len(new_titles)}")

        # 对于每个新标题，找到内容相似度最高的旧标题并替换
        for new_title in new_titles:
            old_title = process.extractOne(new_title, old_titles)[0]
            lines = [line.replace(old_title, new_title + '\n') if line == old_title else line for line in lines]

            print(f"{old_title} ====> {new_title}")

        # 如果不需要保留标题的序号，去掉序号
        if no_number:
            titles = [line for line in lines if line.startswith('#')]
            for title in titles:
                # 用第一个空格分割字符串为前后两部分a和b
                prefix, content = title.split(' ', 1)
                # 对b做处理：若b的首个字符是数字，“.”或者空格，则将其删除，直至b不以这三类字符开头为止
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
    for old_title in old_titles:
        print(old_title)
    # 调用LLM调整标题级别
    new_titles = utils.simple_llm_api_process(
        content="\n".join(old_titles),
        api_key=model.api_key,
        url=model.base_url,
        model=model.model_name,
        prompt="""
                将以下Markdown标题重新调整级别，从1级算起，章节标题与文章标题同设为1级。
                注意：
                - 去掉标题中多余的空白，但不要改变标题内容
                - 如果标题有编号，保留编号不要删掉
                - 直接给出结果，不要输出多余内容
                """
    )
    new_titles = new_titles.split('\n')
    new_titles = [line for line in new_titles if re.match(r"^(#{1,6})\s*(.*)", line)]
    # 询问是否需要去掉标题的序号
    # no_number = input("是否需要去掉标题的序号？(y/n)")
    # if no_number == 'y':
    #     no_number = True
    # else:
    #     no_number = False

    # 打印LLM的输出结果
    # print("LLM输出的新标题：")
    # for new_title in new_titles:
    #     print(new_title)

    # 提示用户选择操作
    while True:
        user_choice = input("请选择操作：1-接受更改，2-重新生成，3-取消操作\n")
        if user_choice == '1':
            output_md_file_path = replace_titles()
            return output_md_file_path
        elif user_choice == '2':
            return arrange_titles(md_file_path, model, replace)
        elif user_choice == '3':
            print("操作已取消。")
            return None
        else:
            print("无效输入，请重新选择。")


if __name__ == '__main__':
    arrange_titles(
        r"C:\Users\XSR_Main\Documents\Obsidian Vault\云容器\微服务异常检测\2021_EN_TraceLingo：云服务性能问题诊断的追踪表示与学习_md\2021_EN_TraceLingo：云服务性能问题诊断的追踪表示与学习.md",
        replace=True)

    '''
    测试
    '''
    # md_file_path = "J:\Study\PostGraduate\云容器\云环境下容器异常检测与访问控制技术研究_杨艺\云环境下容器异常检测与访问控制技术研究_杨艺.md"
    # new_titles = [
    #     '# 摘要',
    #     '# Research on Container Anomaly Detection and Access Control in Cloud Environment',
    #     '# Abstract',
    #     '# 第1章 绪论',
    #     '## 1.1 研究背景及意义',
    #     '## 1.2 国内外研究现状',
    #     '### 1.2.1 容器环境下监控与检测',
    #     '#### (一) 容器镜像检测',
    #     '### 1.2.2 容器环境下的访问控制',
    #     '### 1.2.3 基于硬件的容器安全防护',
    #     '## 1.3 研究动机及研究内容',
    #     '### 1.3.1 研究动机',
    #     '### 1.3.2 研究内容',
    #     '## 1.4 文章结构',
    #     '# 第2章 相关技术',
    #     '## 2.1 Kubernetes 技术',
    #     '## 2.2 容器技术',
    #     '### 2.2.1 Namespace',
    #     '### 2.2.2 CGroup',
    #     '### 2.2.3 容器镜像',
    #     '#### 图2.3 容器镜像组成结构',
    #     '## 2.3 Kprobes 技术',
    #     '### 2.3.1 Kprobes 简介',
    #     '### 2.3.2 Kprobes 原理',
    #     '#### 1) Kprobe',
    #     '#### 表2.2 Kprobe 结构体',
    #     '#### 2) Jprobe',
    #     '#### 3) Kretprobe',
    #     '## 2.4 本章小结',
    #     '# 第3章 容器安全防护框架',
    #     '## 3.1 容器安全风险分析',
    #     '### 1) 容器内进程攻击容器',
    #     '### 2) 容器间攻击',
    #     '### 3) 容器攻击宿主机',
    #     '### 4) 宿主机攻击容器',
    #     '## 3.2 容器安全防护框架',
    #     '### 3.2.1 安全防护分析',
    #     '### 3.2.2 安全防护框架',
    #     '#### 1) 容器行为监控',
    #     '#### 2) 容器异常行为检测',
    #     '#### 3) 容器异常行为控制',
    #     '## 3.3 本章小结',
    #     '# 第4章 基于系统调用和自动编码器的容器异常检测研究',
    #     '## 4.1 基于系统调用和自动编码器的异常检测系统架构',
    #     '## 4.2 基于strace 的容器系统调用采集',
    #     '### 4.2.1 容器系统调用采集',
    #     '#### 表4.1 系统调用采集列表',
    #     '### 4.2.2 数据处理',
    #     '### 4.2.3 数据归一化',
    #     '## 4.3 基于自动编码器和单分类神经网络的异常检测模型',
    #     '### 4.3.1 自动编码器训练',
    #     '### 4.3.2 单分类支持向量机训练',
    #     '### 4.3.3 容器异常行为检测',
    #     '## 4.4 实验分析',
    #     '### 4.4.1 功能测试',
    #     '#### 2) 可视化模型拟合分析',
    #     '#### 3) 异常攻击检测效果',
    #     '### 4.4.2 性能测试',
    #     '### 4.4.3 对比测试',
    #     '## 4.5 本章小结',
    #     '# 第5章 基于Kprobes 和内核函数的容器访问控制方法研究',
    #     '## 5.1 基于Kprobes 和内核函数的容器访问控制框架',
    #     '### 5.1.1 容器环境下访问控制相关定义',
    #     '### 5.1.2 访问控制框架',
    #     '## 5.2 访问策略文件解析',
    #     '## 5.3 基于kprobes 的内核函数监控',
    #     '### 5.3.1 系统调用分级',
    #     '### 5.3.2 内核函数安全风险',
    #     '### 5.3.3 内核函数监控',
    #     '## 5.4 基于内核函数上下文的访问控制算法',
    #     '### 5.4.1 内核函数上下文',
    #     '### 5.4.2 访问控制算法',
    #     '## 5.5 实验',
    #     '### 5.5.1 功能测试',
    #     '### 5.5.2 性能测试',
    #     '### 5.5.3 对比测试',
    #     '## 5.6 本章小结',
    #     '# 第6章 总结与展望',
    #     '## 6.1 总结',
    #     '## 6.2 展望',
    #     '# 参考文献'
    # ]
    # replace_titles(md_file_path, new_titles)
