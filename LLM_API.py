from LLM_tools import LLM_model

# 配置你的Mistral OCR API，用于将PDF转换为Markdown
Mistral_OCR_API = ""

'''
配置你要用的LLM模型，部分主流模型的URL等信息已经配置好，只需要修改APIkey和model_name即可
启动时会自动检测已填写了API key的模型作为可用模型，若可用模型不止1个，则会提示用户选择要使用的模型
如果你想使用其他模型，可以参考下面的格式进行配置
'''
MyLLMs = [
    # DeepSeek
    LLM_model(
        # 具体的模型名
        model_name="deepseek-chat",
        # url地址，默认不需要修改
        post_url="https://api.deepseek.com/v1/chat/completions",
        # 填入你的APIkey
        api_key="",
        # 翻译的并行度，数字越大翻译越快，但也越容易超过并发限制，建议不超过3
        max_concurrent=3,
    ),
    # 通义千问
    LLM_model(
        # 具体的模型名，如qwen-plus
        model_name="qwen-plus",
        # url地址，默认不需要修改
        post_url="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        # 填入你的APIkey
        api_key="",
        # 翻译的并行度，数字越大翻译越快，但也越容易超过并发限制，建议不超过3
        max_concurrent=3,
    ),
    # 智谱清言
    LLM_model(
        # 具体的模型名，如glm-4-plus
        model_name="glm-4-flash",
        # url地址，默认不需要修改
        post_url="https://open.bigmodel.cn/api/paas/v4/chat/completions",
        # 填入你的APIkey
        api_key="",
        # 翻译的并行度，数字越大翻译越快，但也越容易超过并发限制，建议不超过3
        max_concurrent=3,
    ),
    # OpenAI
    LLM_model(
        # 具体的模型名，如gpt-4o
        model_name="gpt-4o",
        # url地址，默认不需要修改
        post_url="https://api.openai.com/v1/chat/completions",
        # 填入你的APIkey
        api_key="",
        # 翻译的并行度，数字越大翻译越快，但也越容易超过并发限制，建议不超过3
        max_concurrent=3,
    ),
    # Google Gemini
    LLM_model(
        # 具体的模型名，如gemini-2.0-flash
        model_name="gemini-2.0-flash",
        # url地址，默认不需要修改
        post_url="https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        # 填入你的APIkey
        api_key="",
        # 翻译的并行度，数字越大翻译越快，但也越容易超过并发限制，建议不超过3
        max_concurrent=1,
    ),
    # Azure
    LLM_model(
        # 具体的模型名
        model_name="gpt-4o-azure",
        # url地址
        post_url="",
        # 填入你的APIkey
        api_key="",
        # 翻译的并行度，数字越大翻译越快，但也越容易超过并发限制，建议不超过3
        max_concurrent=3,
    ),
    # OpenRouter
    LLM_model(
        # 具体的模型名，如deepseek/deepseek-chat-v3-0324:free
        model_name="deepseek/deepseek-chat-v3-0324:free",
        # url地址，默认不需要修改
        post_url="https://api.openrouter.ai/v1/chat/completions",
        # 填入你的APIkey
        api_key="",
        # 翻译的并行度，数字越大翻译越快，但也越容易超过并发限制，建议不超过3
        max_concurrent=1,
    ),
]


def ChooseLLM(MyLLMs):
    """
    通过控制台交互，让用户选择要使用的LLM模型。

    Args:
        MyLLMs: LLM模型列表

    Returns:
        用户选择的LLM_model对象
    """
    # 筛选出api_key不为空的LLM模型
    valid_llms = [llm for llm in MyLLMs if llm.api_key]
    # 若可用模型只有1个，则直接返回
    if len(valid_llms) == 1:
        print(f"自动选择: {valid_llms[0].model_name}")
        return valid_llms[0]

    if not valid_llms:
        print("没有找到有效的LLM模型，请先配置API密钥。")
        return None

    print("可用的LLM模型:")
    for i, llm in enumerate(valid_llms):
        print(f"[{i + 1}] {llm.model_name}")

    while True:
        try:
            choice = int(input("请选择要使用的LLM模型 (输入序号): "))
            if 1 <= choice <= len(valid_llms):
                selected_llm = valid_llms[choice - 1]
                print(f"已选择: {selected_llm.model_name}")
                return selected_llm
            else:
                print(f"请输入1到{len(valid_llms)}之间的数字")
        except ValueError:
            print("请输入有效的数字")


if __name__ == "__main__":
    # 选择LLM模型
    selected_llm = ChooseLLM(MyLLMs)

    if selected_llm:
        print(selected_llm.model_name)
        pass
    else:
        print("没有选择有效的LLM模型，程序结束。")


