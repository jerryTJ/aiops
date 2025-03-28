from typing import Any, List, Optional, Iterator, AsyncIterator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage,AIMessageChunk
from langchain_core.outputs import ChatResult, ChatGeneration, ChatGenerationChunk
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
import requests
import json

class DeepSeekChat(BaseChatModel):
    api_key: str
    base_url: str = "https://api.deepseek.com/v1/chat/completions"
    model: str = "deepseek-chat"
    streaming: bool = True  # 启用流式模式

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        # 转换消息格式
        formatted_messages = [
            {"role": "user" if isinstance(msg, HumanMessage) else "assistant", "content": msg.content}
            for msg in messages
        ]

        # 请求参数中添加 stream=True
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = {
            "model": self.model,
            "messages": formatted_messages,
            "stream": True,  # 关键：启用流式
            **kwargs
        }

        # 发起流式请求
        response = requests.post(self.base_url, json=data, headers=headers, stream=True)
        response.raise_for_status()

        # 逐块解析响应
        for line in response.iter_lines():
            if line:
                chunk = line.decode("utf-8").strip()
                if chunk.startswith("data: "):
                    chunk = chunk[6:]  # 移除 "data: " 前缀
                    if chunk == "[DONE]":
                        break
                    try:
                        json_chunk = json.loads(chunk)
                        content = json_chunk["choices"][0]["delta"].get("content", "")
                        if content:
                            chunk = ChatGenerationChunk(message=AIMessageChunk(content=content))
                            if run_manager:  # 回调处理（如显示进度）
                                run_manager.on_llm_new_token(content)
                            yield chunk
                    except Exception as e:
                        print(f"解析错误: {e}")
    def _common_http(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        # 转换消息格式
        formatted_messages = [
            {"role": "user" if isinstance(msg, HumanMessage) else "assistant", "content": msg.content}
            for msg in messages
        ]
        
        # 调用 API
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = {
            "model": self.model,
            "messages": formatted_messages,
            **kwargs
        }
        response = requests.post(self.base_url, json=data, headers=headers)
        response.raise_for_status()
        # 解析响应并包装为 ChatResult
        result = response.json()
        content = result['choices'][0]['message']['content']
        message = AIMessage(content=content)
        
        # 必须返回 ChatResult 对象
        return ChatResult(
            generations=[ChatGeneration(message=message)]
        )
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        if self.streaming:
            final_content = ""
            for chunk in self._stream(messages, stop, run_manager, **kwargs):
                final_content += chunk.message.content
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=final_content))])
        else:
            return self._common_http(messages, stop, run_manager, **kwargs)

    @property
    def _llm_type(self) -> str:
        if self.streaming:   
            return "deepseek-chat-stream"
        else:
            return "deepseek-chat"