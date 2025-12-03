import uuid
import json
import datetime
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.messages import BaseMessage


class AgentTracer(AsyncCallbackHandler):

    def __init__(self, log_file="trace_log.json"):
        self.trace_id = str(uuid.uuid4())
        self.log_file = log_file
        self.current_step = 0
        self.records = []

        print(f"\033[92m[Tracer Initialized] trace_id = {self.trace_id}\033[0m")

    def to_jsonable(self, obj):
        """Convert LangChain objects to JSON-serializable structure."""
        # 基本类型：直接返回
        if isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj

        # 列表：逐项序列化
        if isinstance(obj, list):
            return [self.to_jsonable(x) for x in obj]

        # 字典：key/value 都序列化
        if isinstance(obj, dict):
            return {k: self.to_jsonable(v) for k, v in obj.items()}

        # LangChain 的消息类型，如 ToolMessage, AIMessage, HumanMessage
        if isinstance(obj, BaseMessage):
            return {
                "type": obj.type,
                "content": obj.content,
                "additional_kwargs": obj.additional_kwargs
            }

        # 兜底：转换为 string
        return str(obj)

    # -------------------------------
    # Utility: save record to memory
    # -------------------------------
    def _save(self, event_type, data):
        record = {
            "trace_id": self.trace_id,
            "step": self.current_step,
            "event": event_type,
            "timestamp": datetime.datetime.now().isoformat(),
            "data": self.to_jsonable(data)
        }
        self.records.append(record)

    # -------------------------------
    # Persist JSON file
    # -------------------------------
    def save_to_file(self):
        with open(self.log_file, "a", encoding="utf-8") as f:
            # f.write(json.dumps(self.records))
            json.dump(self.records, f, indent=2, ensure_ascii=False)
        print(f"\033[94m[Trace Saved] → {self.log_file}\033[0m")

    # -------------------------------
    # LLM Events
    # -------------------------------
    async def on_llm_start(self, serialized, prompts, **kwargs):
        self.current_step += 1
        print(f"\n\033[95m=== Step {self.current_step}: LLM START ===\033[0m")
        print(f"\033[96mPrompt:\033[0m {prompts}")

        self._save("llm_start", {"prompts": prompts})

    async def on_llm_new_token(self, token, **kwargs):
        print(f"\033[93m{token}\033[0m", end="", flush=True)

        self._save("llm_token", {"token": token})

    async def on_llm_end(self, response: LLMResult, **kwargs):
        text = response.generations[0][0].text
        print(f"\n\033[95m=== LLM END ===\033[0m")
        print(f"\033[92mOutput:\033[0m {text}")

        self._save("llm_end", {"output": text})

    # -------------------------------
    # Tool Events
    # -------------------------------
    async def on_tool_start(self, serialized, input_str, **kwargs):
        self.current_step += 1
        tool_name = serialized.get("name")

        print(f"\n\033[94m=== Step {self.current_step}: TOOL START ===\033[0m")
        print(f"Tool: {tool_name}")
        print(f"Input: {input_str}")

        self._save("tool_start", {
            "tool": tool_name,
            "input": input_str
        })

    async def on_tool_end(self, output, **kwargs):
        print(f"Output: {output}")

        self._save("tool_end", {"output": output})

    # -------------------------------
    # Chain / Agent Finish
    # -------------------------------
    async def on_chain_end(self, outputs, **kwargs):
        print(f"\n\033[92m=== Agent Finished ===\033[0m")
        print(f"Final Output: {outputs}")
        self._save("agent_end", {"outputs": outputs})
        # 最后保存 log 文件
        self.save_to_file()
