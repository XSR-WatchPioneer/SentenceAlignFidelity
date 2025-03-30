import utils

def check_paragraphs_breaks(file_path):
    # 逐行读取markdown文件
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # 执行分块
    blocks = utils.split_markdown_into_blocks(lines)

    # 获取所有段落类型的块
    para_blocks = []
    for block in blocks:
        if block[0] == 'paragraph' or block[0] == 'formula':
            para_blocks.append(block)
        # 遇到参考文献就停止
        if block[0] == 'header' and 'references' in block[1].lower():
            break

    # 用于标记是否有问题
    has_issues = False
    # 收集异常段落
    issue_paragraphs = []

    for para in para_blocks:
        # 跳过公式块
        if para[0] == 'formula':
            continue
        content = para[1].strip()
        line_num = lines.index(para[1]) + 1

        # 初始化异常标记
        start_issue = False
        end_issue = False

        # 检查开头
        if (not content[0].isupper()
                and not content[0] == '-'
                and not content[0].isdigit()
                and not content[0] == '['
                and not content.lower().startswith('where')
        ):
            start_issue = True
            has_issues = True

        # 检查结尾
        punctuation = '.!?;:"\''
        if not content[-1] in punctuation:
            # 检查下一个Block是否为formula
            next_block_index = para_blocks.index(para) + 1
            if not (next_block_index < len(para_blocks) and para_blocks[next_block_index][0] == 'formula'):
                end_issue = True
                has_issues = True

        # 如果存在异常，记录信息
        if start_issue or end_issue:
            issue_paragraphs.append({
                '内容': content,
                '开头异常': start_issue,
                '结尾异常': end_issue,
                '行号': line_num
            })

    # 获取参考文献块，参考文献块是Reference标题下的所有paragraph块
    ref_blocks = []
    for i, block in enumerate(blocks):
        if block[0] == 'header' and 'references' in block[1].lower():
            for j in range(i + 1, len(blocks)):
                if blocks[j][0] == 'paragraph':
                    ref_blocks.append(blocks[j])
                else:
                    break
            break
    # 检查开头是否以[开头
    for para in ref_blocks:
        content = para[1].strip()
        line_num = lines.index(para[1]) + 1

        # 检查开头是否以数字或[开头
        if content[0] != '[' and not content[0].isdigit():
            has_issues = True
            issue_paragraphs.append({
                '内容': content,
                '引用异常': True,
                '行号': line_num
            })

    return issue_paragraphs


# 交互版本
def check_paragraphs_breaks_interactive(file_path):
    # # 将文本中所有的'$ '和' $'替换为'$'
    # utils.replace_all(file_path, '$ ', '$')
    # utils.replace_all(file_path, ' $', '$')
    while True:
        # 逐行读取markdown文件
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # 执行分块
        blocks = utils.split_markdown_into_blocks(lines)

        # 获取所有段落类型的块
        # para_blocks = [block for block in blocks if block[0] == 'paragraph']
        para_blocks = []
        for block in blocks:
            if block[0] == 'paragraph' or block[0] == 'formula':
                para_blocks.append(block)
            # 遇到参考文献就停止
            if block[0] == 'header' and 'references' in block[1].lower():
                break

        # 用于标记是否有问题
        has_issues = False
        # 收集异常段落
        issue_paragraphs = []

        for para in para_blocks:
            # 跳过公式块
            if para[0] == 'formula':
                continue
            content = para[1].strip()
            line_num = lines.index(para[1]) + 1

            # 初始化异常标记
            start_issue = False
            end_issue = False

            # 检查开头
            if (not content[0].isupper()
                    and not content[0] == '-'
                    and not content[0].isdigit()
                    and not content[0] == '['
                    and not content.lower().startswith('where')
            ):
                start_issue = True
                has_issues = True

            # 检查结尾
            punctuation = '.!?;:"\''
            if not content[-1] in punctuation:
                # 检查下一个Block是否为formula
                next_block_index = para_blocks.index(para) + 1
                if not (next_block_index < len(para_blocks) and para_blocks[next_block_index][0] == 'formula'):
                    end_issue = True
                    has_issues = True

            # 如果存在异常，打印带有突出显示的内容
            if start_issue or end_issue:
                issue_paragraphs.append({
                    '内容': content,
                    '开头异常': start_issue,
                    '结尾异常': end_issue,
                    '行号': line_num
                })
                if start_issue and end_issue:
                    # 开头和结尾都有问题
                    if len(content) <= 10:
                        print(f"\033[1;34m{content}\033[0m")
                    else:
                        print(f"\033[1;34m{content[:5]}\033[0m{content[5:-5]}\033[1;34m{content[-5:]}\033[0m")
                elif start_issue:
                    # 只有开头有问题
                    if len(content) <= 5:
                        print(f"\033[1;34m{content}\033[0m")
                    else:
                        print(f"\033[1;34m{content[:5]}\033[0m{content[5:]}")
                else:
                    # 只有结尾有问题
                    if len(content) <= 5:
                        print(f"\033[1;34m{content}\033[0m")
                    else:
                        print(f"{content[:-5]}\033[1;34m{content[-5:]}\033[0m")
                print()

        # 获取参考文献块，参考文献块是Reference标题下的所有paragraph块
        ref_blocks = []
        for i, block in enumerate(blocks):
            if block[0] == 'header' and 'references' in block[1].lower():
                for j in range(i + 1, len(blocks)):
                    if blocks[j][0] == 'paragraph':
                        ref_blocks.append(blocks[j])
                    else:
                        break
                break
        # 检查开头是否以[开头
        for para in ref_blocks:
            content = para[1].strip()
            line_num = lines.index(para[1]) + 1

            # 检查开头是否以数字或[开头
            if content[0] != '[' and not content[0].isdigit():
                has_issues = True
                issue_paragraphs.append({
                    '内容': content,
                    '引用异常': True,
                    '行号': line_num
                })
                print(f"\033[1;31m行号 {line_num} 参考文献开头可能异常:\033[0m")
                if len(content) >= 5:
                    print(f"\033[1;34m{content[:5]}\033[0m{content[5:]}")
                else:
                    print(f"{content}")

        if not has_issues:
            # 用绿色字体输出检查通过
            print("\033[1;32m====段落断开检查通过====\033[0m")
            return []

        # 输入exit退出，否则继续执行检查
        # 用蓝色显示
        user_input = input("\033[1;34m输入任意内容执行检查，输入exit退出\033[0m")
        if user_input.lower() == 'exit':
            break

    return issue_paragraphs


if __name__ == '__main__':
    issues = check_paragraphs_breaks(utils.select_md())
    print(issues)
