import os
import random
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from difflib import SequenceMatcher
from pathlib import Path

from LLM_API import *
from utils import split_markdown_into_blocks, merge_by_top_section, count_words, clean_filename, select_md_files, select_md_or_pdf_files
from Autoadjust_title import arrange_titles
from Mistral_OCR import process_pdf, Mistral_OCR_API


def recover_paragraph(translated_file_path, original_blocks):
    """
    恢复翻译后文件的段落格式
    Args:
        translated_file_path: 翻译后的文件路径
        original_blocks: 原文的blocks
    """
    # 读取翻译后的文件
    with open(translated_file_path, 'r', encoding='utf-8') as f:
        translated_content = f.readlines()

    # 解析翻译后的内容为blocks
    translated_blocks = split_markdown_into_blocks(translated_content)

    # 提取原文中的paragraph blocks及其开头内容
    original_paragraphs = []
    for i, block in enumerate(original_blocks):
        if block[0] == 'paragraph':
            # 提取开头的N个字符作为匹配特征
            preview = block[1][:100] if len(block[1]) > 100 else block[1]
            original_paragraphs.append((i, preview, block))

    # 提取翻译后的paragraph blocks
    translated_paragraphs = []
    for i, block in enumerate(translated_blocks):
        if block[0] == 'paragraph':
            translated_paragraphs.append((i, block[1]))

    # 对每个原文paragraph找到最匹配的译文paragraph
    matches = []
    for orig_idx, orig_preview, orig_block in original_paragraphs:
        best_match_score = 0
        best_match_idx = -1

        # 使用SequenceMatcher查找最佳匹配
        for trans_idx, trans_content in translated_paragraphs:
            # 比较原文预览与译文开头的相似度
            matcher = SequenceMatcher(None, orig_preview,
                                      trans_content[:100] if len(trans_content) > 100 else trans_content)
            score = matcher.ratio()

            if score > best_match_score:
                best_match_score = score
                best_match_idx = trans_idx

        if best_match_idx != -1:
            matches.append((orig_idx, best_match_idx))

    # 按原文顺序排序匹配结果
    matches.sort(key=lambda x: x[0])

    # 构建新的输出内容
    output_content = []

    for trans_idx, block in enumerate(translated_blocks):
        # 如果当前block是已匹配的paragraph
        if block[0] == 'paragraph' and any(m[1] == trans_idx for m in matches):
            # 添加额外的换行符
            output_content.append('\n')
        output_content.append(block[1])
    # 覆写文件
    with open(translated_file_path, 'w', encoding='utf-8') as f:
        f.writelines(output_content)

    # print(f"段落格式已恢复，结果保存至: {translated_file_path}")
    return translated_file_path


def translate_references(section, block_file, model: LLM_model = gpt_4o_mini_AzureOpenAI, max_translation=1000):
    #todo 若原文的参考文献断行有异常，则无法使用
    """专门处理参考文献章节，分批翻译并验证结果"""
    def translate_batch(text_batch):
        """处理单批次翻译"""
        system_prompt = """你是专业的参考文献翻译器。请将英文参考文献条目翻译成中文。
        注意：
        - 保持原有格式，包括换行、缩进和标点
        - 保持原有的引用编号格式
        - 直接输出译文，不要有任何解释"""

        result = LLM_Stream_Response(
            model=model,
            system_prompt=system_prompt,
            prompt=f"翻译以下参考文献：\n{text_batch}",
            write_file=block_file,
            timeout=10,
            max_tokens=4095
        )

        if result is None:
            print("批次翻译出错")
            return None
        else:
            translated_text, token_usage = result
            return translated_text

    def validate_translation(translated_blocks, original_blocks):
        """验证翻译结果"""
        if len(translated_blocks) != len(original_blocks):
            return False
        for trans_block, orig_block in zip(translated_blocks, original_blocks):
            if trans_block[0] != orig_block[0]:
                return False
        return True

    # 清空输出文件
    open(block_file, 'w', encoding='utf-8').close()

    max_retries = 3
    current_text = ""
    current_words = 0
    batch_contents = []

    # 将翻译的内容分批
    for block in section:
        block_type, block_content = block
        current_text += block_content + '\n'
        current_words += count_words(block)

        if current_words >= max_translation or block == section[-1]:
            batch_contents.append(current_text)
            current_text = ""
            current_words = 0

    # 对每个批次进行翻译和验证
    for retry in range(max_retries):
        translated_content = ""
        open(block_file, 'w', encoding='utf-8').close()  # 清空文件

        # 翻译每个批次
        for batch in batch_contents:
            translated_batch = translate_batch(batch)
            if translated_batch is None:
                break
            translated_content += translated_batch + "\n"

        # 解析翻译结果
        translated_blocks = split_markdown_into_blocks(translated_content.split('\n'))

        # 验证翻译结果
        if validate_translation(translated_blocks, section):
            print(f"参考文献翻译成功（第{retry + 1}次尝试）")
            # 重新处理内容：将译文和原文对照
            final_content = []
            for trans_block, orig_block in zip(translated_blocks, section):
                if trans_block[0] == "paragraph" and orig_block[0] == "paragraph":
                    if trans_block[1].lstrip().startswith('[') and orig_block[1].lstrip().startswith('['):
                        final_content.append(f"{trans_block[1].rstrip()} ==> {orig_block[1]}")
                    else:
                        final_content.append(trans_block[1])
                else:
                    final_content.append(orig_block[1])

            # 写入最终结果
            with open(block_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(final_content))
            return block_file

        print(f"参考文献翻译验证失败（第{retry + 1}次尝试），准备重试...")
        time.sleep(random.uniform(2, 5))

    # 所有重试都失败，使用原文
    print("参考文献翻译失败，使用原文")
    with open(block_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(block[1] for block in section))
    return block_file


def TranslateProcess(section, idx, file_dir, max_translation=1000, model: LLM_model = glm_4_plus, md_file_name=""):
    """
    处理单个块的翻译过程，并将结果写入文件
    Args:
        section: 待处理的section内容（块列表）
        idx: section序号
        file_dir: 输出目录
        max_translation: 最大翻译字数
        model: LLM模型
        md_file_name: 原始Markdown文件名（不含扩展名）
    Returns:
        str: 生成的块文件路径
    """
    SYS_PROMPT = """
你是专业从事学术论文翻译的高技能翻译引擎。你的职责是将学术文本翻译成中文，确保复杂概念和专业术语的准确翻译，而不改变原有的学术语气或添加解释。
注意:
- 保持和原文格式一致。
- 不要擅自合并或拆分段落。
- 不要擅自添加标题。
- 不要有漏译。

你将以逐句对照的形式给出翻译，要求原文一句，译文一句，原文在上，英文在下
"""

    # 提取标题文本
    title_text = "untitled"
    for block in section:
        if block[0] == 'header' and block[1].startswith('#'):
            title_text = block[1].strip('#').strip()
            break

    # 清理并限制标题长度
    safe_title = clean_filename(title_text)[:30]

    # 创建块文件
    block_file = os.path.join(file_dir, f"block_{idx:02d}_{safe_title}_{md_file_name}.md")

    """处理参考文献章节"""
    # 检查是否为参考文献章节
    is_references = False
    for block in section:
        if block[0] == 'header' and title_text == '参考文献':
            is_references = True
            break

    if is_references:
        # 使用专门的参考文献处理函数
        # translate_references(section, block_file)
        # return block_file
        # 不翻译，直接写入
        with open(block_file, 'w', encoding='utf-8') as f:
            for block in section:
                f.write(block[1] + '\n')
        return block_file


    # 初始化对话历史
    # todo 保持对话历史不超过5轮
    conversation_history = [
        {"role": "system", "content": SYS_PROMPT},
        {"role": "user",
         "content": f"A microservice system in industry is usually a large-scale distributed system consisting of dozens to thousands of services running in different machines. An anomaly of the system often can be reflected in traces and logs, which record inter-service interactions and intra-service behaviors respectively.Existing trace anomaly detection approaches treat a trace as a sequence of service invocations. They ignore the complex structure of a trace brought by its invocation hierarchy and parallel/asynchronous invocations."},
        {"role": "assistant", "content": """A microservice system in industry is usually a large-scale distributed system consisting of dozens to thousands of services running in different machines.
工业中的微服务系统通常是由数十到数千个服务在不同机器上运行的大规模分布式系统。
An anomaly of the system often can be reflected in traces and logs, which record inter-service interactions and intra-service behaviors respectively.
系统的异常通常可以在痕迹和日志中反映出来，分别记录服务间交互和服务内行为。
Existing trace anomaly detection approaches treat a trace as a sequence of service invocations.
现有的痕迹异常检测方法将痕迹视为服务调用的序列。
They ignore the complex structure of a trace brought by its invocation hierarchy and parallel/asynchronous invocations.
它们忽略了痕迹因调用层次结构和并行/异步调用带来的复杂结构。"""},
    ]

    def translate_text(text_to_translate):
        """执行实际的翻译请求"""
        # 添加用户消息到对话历史
        conversation_history.append({"role": "user", "content": f"{text_to_translate}"})

        # 调用新的LLM_Stream_Response函数
        result = LLM_Stream_Response(
            model=model,
            messages=conversation_history,
            write_file=block_file,
            timeout=30,
            max_tokens=4095
        )

        # 处理响应
        if result is None:
            # 所有重试都失败，写入原文
            with open(block_file, 'a', encoding='utf-8') as f:
                f.write(text_to_translate)
                f.write(f"\n[翻译出错，使用原文]\n")
            # 移除失败的用户消息
            conversation_history.pop()
            return
        # 解析翻译结果
        translated_content, token_usage = result

        # 记录assistant的完整回复，用于下一次对话
        conversation_history.append({"role": "assistant", "content": translated_content})

    # 处理每个块
    current_text = ""
    current_words = 0

    for block in section:
        block_type, block_content = block

        # 如果遇到非paragraph类型，先处理已累积的内容
        if block_type != 'paragraph':
            if current_text:
                # 先翻译已累积的段落
                translate_text(current_text)
                current_text = ""
                current_words = 0

            # 直接写入非paragraph内容
            with open(block_file, 'a', encoding='utf-8') as f:
                f.write('\n' + block_content + '\n\n')
            continue

        # 处理paragraph类型
        words_count = count_words(block)

        # 如果累积内容将超过限制，先翻译当前累积的内容
        if current_words + words_count > max_translation and current_text:
            translate_text(current_text)
            current_text = ""
            current_words = 0

        # 累积内容
        current_text += block_content + '\n'
        current_words += words_count

        # 如果累积内容达到上限，进行翻译
        if current_words >= max_translation:
            translate_text(current_text)
            current_text = ""
            current_words = 0

    # 翻译剩余内容
    if current_text:
        translate_text(current_text)

    # 恢复分段
    recover_paragraph(block_file, section)

    return block_file


def check_titles_consistency(orig_titles, translated_titles):
    """检查原始标题和翻译后的标题是否一致"""
    if len(orig_titles) != len(translated_titles):
        return False

    for orig, trans in zip(orig_titles, translated_titles):
        # 检查标题等级（#的数量）是否一致
        orig_level = len(orig[1].split()[0])  # 计算#的数量
        trans_level = len(trans[1].split()[0])  # 计算#的数量
        if orig_level != trans_level:
            return False
    return True


def translate_titles(title_blocks, model: LLM_model):
    """翻译标题块"""
    title_text = "\n".join(block[1] for block in title_blocks)

    system_prompt = """你是专业的Markdown文档标题翻译器。
请将给定的英文标题翻译成中文，注意：
1. 保持原有的标题等级（#的数量）不变
2. 保持原有的标题序号（如果有）不变
3. 每个标题占一行
4. 直接输出翻译结果，不要有任何解释
"""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 使用新的LLM_Stream_Response函数
            result = LLM_Stream_Response(
                model=model,
                system_prompt=system_prompt,
                prompt=f"翻译以下Markdown标题：\n{title_text}",
                temperature=0.3
            )

            if result is None:
                print(f"第{attempt + 1}次翻译标题失败，准备重试...")
                continue

            translated_text, _ = result

            # 解析翻译后的标题
            translated_titles = []
            for line in translated_text.split('\n'):
                line = line.strip()
                if line and line.startswith('#'):
                    translated_titles.append(('header', line))

            # 检查翻译结果是否符合要求
            if check_titles_consistency(title_blocks, translated_titles):
                return translated_titles

            print(f"第{attempt + 1}次翻译的标题结构不符合要求，重试...")

        except Exception as e:
            print(f"翻译标题时出错: {str(e)}")

        time.sleep(2)

    print("翻译标题失败，将保持原标题不变")
    return title_blocks


from tqdm.auto import tqdm


def process_markdown_translation(md_file_path, max_translation=1000, max_concurrent=3, model: LLM_model = glm_4_plus):
    """
    处理Markdown文件的翻译
    Args:
        md_file_path: Markdown文件路径
        max_concurrent: 最大并行数
    """
    # 获取Markdown文件名（不含扩展名）
    md_file_name = os.path.splitext(os.path.basename(md_file_path))[0]

    # 读取文件内容
    with open(md_file_path, 'r', encoding='utf-8') as file:
        content = file.readlines()

    # 分析文件路径
    file_dir = os.path.dirname(md_file_path)

    # 按照markdown块分割
    blocks = split_markdown_into_blocks(content)

    # 检查一级标题数量
    level1_count = sum(1 for t, c in blocks if t == 'header' and c.startswith('# '))
    if level1_count <= 1:
        print("检测到一级标题数量不足，正在调整标题层级...")
        # 调整标题层级，gemini做不来，只能用gpt-4
        arrange_titles(md_file_path, model=gpt_4o_GitHub)
        with open(md_file_path, 'r', encoding='utf-8') as file:
            content = file.readlines()
        # 重新读取调整后的内容
        blocks = split_markdown_into_blocks(content)
        print("标题层级调整完成")

    # 提取并翻译标题块
    title_blocks = [(t, c) for t, c in blocks if t == 'header']

    if title_blocks:
        print("正在翻译文档标题...")
        translated_titles = translate_titles(title_blocks, model)

        # 替换原文中的标题
        title_index = 0
        for i, (block_type, _) in enumerate(blocks):
            if block_type == 'header':
                blocks[i] = translated_titles[title_index]
                title_index += 1
        print("标题翻译+替换完成")

    # 按照一级标题合并块
    sections = merge_by_top_section(blocks)

    # 并行处理翻译
    block_files = []
    with ProcessPoolExecutor(max_workers=max_concurrent) as executor:
        futures = {
            executor.submit(
                TranslateProcess,
                section,
                idx,
                file_dir,
                max_translation,
                model,
                md_file_name  # 传递Markdown文件名
            ): idx
            for idx, section in enumerate(sections)
        }

        # 使用tqdm显示进度
        for future in tqdm(as_completed(futures), total=len(sections), desc="翻译进度"):
            idx = futures[future]
            try:
                block_file = future.result()
                block_files.append(block_file)
            except Exception as e:
                print(f"\n处理章节 {idx + 1} 时出错: {str(e)}")

    # 按序号排序文件列表
    block_files.sort(key=lambda x: os.path.basename(x))

    '''合并翻译结果'''
    base_name = os.path.splitext(os.path.basename(md_file_path))[0]
    #调整文件名
    if '_EN_' in base_name:
        base_name = base_name.replace('_EN_', '_CH_')
    output_file = os.path.join(file_dir, f"{base_name}_逐句对照.md")

    # 执行断行检查
    from Abnormal_line_breaking_check import check_paragraphs_breaks
    print("执行断行检查...")
    issues = check_paragraphs_breaks(md_file_path)

    # 写入断行检查结果和翻译内容
    with open(output_file, 'w', encoding='utf-8') as outfile:
        # 首先写入断行检查结果
        outfile.write("# 断行检查结果\n\n")
        if issues:
            outfile.write("发现以下异常断行：\n\n")
            for issue in issues:
                outfile.write(f"- 行号 {issue['行号']}: {issue['内容']}\n")
                if issue.get('开头异常'):
                    outfile.write("  - 开头异常\n")
                if issue.get('结尾异常'):
                    outfile.write("  - 结尾异常\n")
                if issue.get('引用异常'):
                    outfile.write("  - 引用格式异常\n")
        else:
            outfile.write("未发现异常断行\n")
        outfile.write("\n---\n\n")

        # 然后写入翻译内容
        for block_file in block_files:
            with open(block_file, 'r', encoding='utf-8') as infile:
                outfile.write(infile.read())
                outfile.write('\n')
            # 删除临时块文件
            # os.remove(block_file)

    print(f"翻译完成，最终结果已保存至: {output_file}")


def auto_batch_translation(input_dir, model=gemini_2_flash):
    """
    自动批量翻译指定文件夹下的Markdown文件
    Args:
        input_dir: 输入文件夹路径
        model: 要使用的翻译模型
    """
    # 首先收集所有符合条件的文件
    target_files = []
    print(f"开始遍历文件夹收集目标文件: {input_dir}")

    for root, dirs, files in os.walk(input_dir):
        md_files = [f for f in files if f.endswith('.md')]
        if len(md_files) == 1:
            md_file = os.path.join(root, md_files[0])
            # 文件名需含有_EN_
            if '_EN_' in md_file and '笔记' not in md_file:
                target_files.append(md_file)
    print(f"找到 {len(target_files)} 个需要处理的文件")
    for file in target_files:
        print(file)

    # 逐个处理收集到的文件
    total_processed = 0
    for md_file in target_files:
        print(f"\n处理文件 [{total_processed + 1}/{len(target_files)}]: {md_file}")
        try:
            process_markdown_translation(md_file, max_translation=800, max_concurrent=1, model=model)
            total_processed += 1
            print(f"已完成 {total_processed}/{len(target_files)} 个文件的翻译")
        except Exception as e:
            print(f"处理文件 {md_file} 时出错: {str(e)}")

    print(f"\n翻译完成，共处理 {total_processed}/{len(target_files)} 个文件")
    return total_processed


if __name__ == "__main__":
    files = select_md_or_pdf_files()
    total_files = len(files)
    for i, file_path in enumerate(files):
        print(f"\n[{i + 1}/{total_files}] 开始处理文件: {os.path.basename(file_path)}")
        start_time = time.time()
        
        # 检查文件类型
        if file_path.lower().endswith('.pdf'):
            print(f"检测到PDF文件，正在使用Mistral OCR进行文本提取...")
            try:
                process_pdf(file_path, Mistral_OCR_API)
                # 获取生成的Markdown文件路径
                md_file_path = Path(file_path).with_suffix('.md')
                if md_file_path.exists():
                    print(f"PDF转Markdown成功，开始翻译处理...")
                    process_markdown_translation(str(md_file_path), max_translation=800, max_concurrent=1, model=gemini_2_flash)
                else:
                    print(f"PDF转Markdown失败，未找到生成的Markdown文件")
            except Exception as e:
                print(f"PDF处理出错: {str(e)}")
        elif file_path.lower().endswith('.md'):
            # 直接处理Markdown文件
            process_markdown_translation(file_path, max_translation=800, max_concurrent=1, model=gemini_2_flash)
        else:
            print(f"不支持的文件类型: {file_path}")
            continue
            
        elapsed_time = time.time() - start_time
        print(f"[{i + 1}/{total_files}] 文件处理完成: {os.path.basename(file_path)}")
        print(f"处理耗时: {elapsed_time:.2f}秒 ({elapsed_time / 60:.2f}分钟)")
        print(f"总体进度: {(i + 1) / total_files * 100:.1f}% 完成")

    # auto_batch_translation(input_dir=r"C:\Users\XSR_Main\Documents\Obsidian Vault\云容器", model=gemini_2_flash)

    # 测试恢复分段
    # process_markdown_translation(md_file_path=r"测试Markdown/test_恢复分段.md",
    #                              max_translation=800, max_concurrent=5, model=qwen_max_0125
    #                              )
