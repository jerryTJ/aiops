
from langchain_openai import ChatOpenAI
from pathlib import Path


class BaseAgent:
    deepseek_api_key = ""  # 替换为你的 DeepSeek API Key
    base_url = "https://api.deepseek.com"

    def __init__(self, deepseek_api_key=None, base_url=None):
        self.deepseek_api_key = deepseek_api_key or self.deepseek_api_key
        self.base_url = base_url or self.base_url

    def load_system_prompt(self, file_path: str) -> str:
        """
        从文件中读取 system prompt
        
        Args:
            file_path: system prompt 文件路径
            
        Returns:
            system prompt 内容
        """
        try:
            path = Path(file_path)
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    print(f"Loaded system prompt from: {file_path}")
                    return content
            else:
                return self._get_default_system_prompt()
        except Exception as e:
            print(f"Error loading system prompt: {e}, using default")
            return self.get_default_system_prompt()

    def _get_default_system_prompt(self) -> str:
        """获取默认的 system prompt"""
        return """
        默认提示词
        """

    def create_deepseek(self):
       
        # Create agent with your MCP tools
        # 初始化 DeepSeek 模型
        llm = ChatOpenAI(
            model="deepseek-chat",  # DeepSeek 模型
            # model="deepseek-reasoner",  # DeepSeek 模型
            temperature=0,
            openai_api_key=self.deepseek_api_key,
            openai_api_base=self.base_url,  # DeepSeek API 地址
            model_kwargs={
                "top_p": 0.95,
            }
        )
        return llm

