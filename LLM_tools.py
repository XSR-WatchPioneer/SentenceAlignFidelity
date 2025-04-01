import json
import time
from typing import Optional, Tuple, Dict, List, Any

import requests
from openai import OpenAI


class LLM_basic:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
        self.post_url = base_url + "/chat/completions"


class LLM_model:
    def __init__(self, model_name, api_key="",post_url=None,LLM: LLM_basic =None , max_concurrent=2, max_translations=1000):
        self.model_name = model_name
        if LLM:
            self.api_key = LLM.api_key
            self.base_url = LLM.base_url
            self.post_url = LLM.post_url
        self.api_key = api_key
        if post_url:
            self.post_url = post_url
        self.max_concurrent = max_concurrent
        self.max_translations = max_translations

    def set_max_concurrent(self, max_concurrent):
        self.max_concurrent = max_concurrent

    def set_max_translations(self, max_translations):
        self.max_translations = max_translations

    def test_by_client(self):
        client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )
        completion = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "编一个50字的故事。"},
            ],
            stream=True,
        )
        content = ""
        for chunk in completion:
            if chunk.choices:
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content:
                    content += chunk.choices[0].delta.content
                    print(delta.content, end='', flush=True)
        return content

    def test_by_http(self, prompt="编一个50字的故事。"):
        """
        通过HTTP流式调用OpenAI的API，并打印接收到的回答。
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "api-key": self.api_key,
        }

        data = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True
        }

        # 发送POST请求并启用流式接收
        with requests.post(self.post_url, headers=headers, json=data, stream=True) as response:
            response.raise_for_status()

            # 遍历流式响应的内容
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data: "):
                        decoded_line = decoded_line[len("data: "):]  # 移除前缀
                        if decoded_line == "[DONE]":
                            break
                        try:
                            json_data = json.loads(decoded_line)
                            if json_data.get('choices'):
                                delta = json_data['choices'][0]['delta']
                                if 'content' in delta:
                                    print(delta['content'], end='', flush=True)
                        except json.JSONDecodeError:
                            continue

    def test_translation(self, text):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "api-key": self.api_key,
        }

        data = {
            "model": self.model_name,
            # 多轮对话
            "messages": [
                {"role": "system", "content": """
                        你是专业从事学术论文翻译的高技能翻译引擎。你的职责是将学术文本翻译成中文，确保复杂概念和专业术语的准确翻译，而不改变原有的学术语气或添加解释。
                        注意:
                        - 保持和原文格式一致。
                        - 对于公式、代码块、链接、请保留原文，不用翻译。
                        - 不要有漏译。
                        """},
                {"role": "user", "content": f"将下面的源文本翻译为中文，直接输出翻译结果：{text}"}
            ],
            "stream": True
        }
        #记录用时
        start_time = time.time()
        # 发送POST请求并启用流式接收
        with requests.post(self.post_url, headers=headers, json=data, stream=True) as response:
            response.raise_for_status()

            # 遍历流式响应的内容
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data: "):
                        decoded_line = decoded_line[len("data: "):]  # 移除前缀
                        if decoded_line == "[DONE]":
                            break
                        try:
                            json_data = json.loads(decoded_line)
                            if json_data.get('choices'):
                                delta = json_data['choices'][0]['delta']
                                if 'content' in delta:
                                    print(delta['content'], end='', flush=True)
                        except json.JSONDecodeError:
                            continue
        #打印用时
        print(f"用时:{time.time() - start_time}")

    def test_whole_translation(self, context, text):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "api-key": self.api_key,
        }

        data = {
            "model": self.model_name,
            # 多轮对话
            "messages": [
                {"role": "system", "content": """
                        你是专业从事学术论文翻译的高技能翻译引擎。你的职责是将学术文本翻译成中文，确保复杂概念和专业术语的准确翻译，而不改变原有的学术语气或添加解释。
                        注意:
                        - 保持和原文格式一致。
                        - 对于公式、代码块、链接、请保留原文，不用翻译。
                        - 不要有漏译。
                        """},
                {"role": "user", "content": context},
                {"role": "assistant", "content": "好的，我已了解的全文语境。"},
                {"role": "user", "content": f"将下面的源文本翻译为中文，直接输出翻译结果：{text}"}
            ],
            "stream": True
        }
        #记录用时
        start_time = time.time()
        # 发送POST请求并启用流式接收
        with requests.post(self.post_url, headers=headers, json=data, stream=True) as response:
            response.raise_for_status()

            # 遍历流式响应的内容
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data: "):
                        decoded_line = decoded_line[len("data: "):]  # 移除前缀
                        if decoded_line == "[DONE]":
                            break
                        try:
                            json_data = json.loads(decoded_line)
                            if json_data.get('choices'):
                                delta = json_data['choices'][0]['delta']
                                if 'content' in delta:
                                    print(delta['content'], end='', flush=True)
                        except json.JSONDecodeError:
                            continue
        #打印用时
        print(f"用时:{time.time() - start_time}")

    # 流式输出至指定文件
    def stream_out_to_file(self, prompt, output_file, system_prompt="你是个AI助手", max_tokens=4095):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "api-key": self.api_key,
        }

        data = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}],
            "stream": True,
            "max_tokens": max_tokens,
        }

        with requests.post(self.post_url, headers=headers, json=data, stream=True) as response:
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data: "):
                        decoded_line = decoded_line[len("data: "):]
                        if decoded_line == "[DONE]":
                            break
                        try:
                            json_data = json.loads(decoded_line)
                            if json_data.get('choices'):
                                delta = json_data['choices'][0]['delta']
                                if 'content' in delta:
                                    content = delta['content']
                                    # print(content, end='', flush=True)
                                    with open(output_file, 'a', encoding='utf-8') as f:
                                        f.write(content)
                        except json.JSONDecodeError:
                            continue
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write("\n")

def LLM_Stream_Response(
        model: LLM_model,
        system_prompt = "You're a helpful assistant.",prompt = None,
        messages: List[Dict[str, str]] = None,
        write_file = None,
        max_tokens = 4096,max_retry: int = 3,timeout = 10,
        temperature: float = 0.7
) -> tuple[str | Any, Any] | None:
    """
    # todo 有些模型不返回token统计信息，如Azure、GitHubModels
    流式调用LLM API并返回结果

    Args:
        model: LLM_Model对象，包含api_key、model_name和post_url
        system_prompt: 系统提示
        prompt: 用户提示
        messages: 对话历史，如果提供则忽略system_prompt和prompt
        write_file: 写入结果的文件路径，如果提供则以追加形式写入
        max_retry: 最大重试次数
        temperature: 温度参数
        max_tokens: 最大生成token数
        timeout: 请求超时时间(秒)

    Returns:
        tuple: (生成的文本内容, token统计字典)
        如果调用失败，返回(None, None)
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {model.api_key}"
    }

    # 准备请求数据
    if messages is None:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if prompt:
            messages.append({"role": "user", "content": prompt})

    data = {
        "model": model.model_name,
        "messages": messages,
        "stream": True,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    response_content = ""
    retry_count = 0
    token_stats = None

    while retry_count < max_retry:
        try:
            with requests.post(
                model.post_url,
                headers=headers,
                json=data,
                stream=True,
                timeout=timeout
            ) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if not line:
                        continue

                    decoded_line = line.decode('utf-8')
                    if not decoded_line.startswith("data: "):
                        continue

                    decoded_line = decoded_line[len("data: "):]
                    if decoded_line == "[DONE]":
                        break

                    try:
                        json_data = json.loads(decoded_line)

                        if json_data.get('choices'):
                            delta = json_data['choices'][0].get('delta', {})

                            if 'content' in delta:
                                content = delta['content']
                                response_content += content

                                # 如果指定了文件，则写入
                                if write_file:
                                    with open(write_file, 'a', encoding='utf-8') as f:
                                        f.write(content)

                        # 获取token统计（通常在最后一个数据块中）
                        if json_data.get('usage'):
                            token_stats = json_data['usage']
                    except json.JSONDecodeError:
                        continue

            # 请求成功，返回结果
            return response_content, token_stats
            # return response_content, token_stats['prompt_tokens'], token_stats['completion_tokens'], token_stats['total_tokens']

        except Exception as e:
            retry_count += 1
            print(f"调用API失败 (尝试 {retry_count}/{max_retry}): {e}")
            if retry_count < max_retry:
                # 指数退避重试
                time.sleep(2 ** retry_count)
    return None