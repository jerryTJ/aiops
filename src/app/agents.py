from langchain.chat_models import ChatOpenAI
from langchain.schema.runnable import RunnableLambda
from langchain.schema import HumanMessage, AIMessage
import asyncio
from langgraph.graph import StateGraph, END

# 模拟商品数据库
PRODUCTS = {
    "iPhone 15": 7999,
    "MacBook Air": 9999,
    "AirPods Pro": 1999,
}

# 客服 Agent
def customer_agent_fn(state):
    user_input = state["input"]
    for product, price in PRODUCTS.items():
        if product.lower() in user_input.lower():
            state["product"] = product
            state["price"] = price
            state["ask"] = f"{product} 价格是 {price} 元，是否需要帮您下单？（回复：是/否）"
            return state
    state["ask"] = "未找到您说的商品，请重新输入。"
    return state

# 下单 Agent
def order_agent_fn(state):
    if state.get("confirmation", "").lower() == "是" and "product" in state:
        state["order_status"] = f"已为您下单 {state['product']}，价格 {state['price']} 元。"
    else:
        state["order_status"] = "已取消下单。"
    return state


# 定义共享状态
class ChatState(dict):
    input: str = ""
    product: str = ""
    price: int = 0
    ask: str = ""
    confirmation: str = ""
    order_status: str = ""

async def main():
    # 创建 StateGraph
    builder = StateGraph(ChatState)

    builder.add_node("CustomerAgent", customer_agent_fn)
    builder.add_node("OrderAgent", order_agent_fn)

    builder.add_edge("CustomerAgent", "OrderAgent")
    builder.add_edge("OrderAgent", END)

    graph = builder.compile()

    # 模拟用户交互
    user_input = input("请输入您要购买的商品：")
    result = await graph.ainvoke({"input": user_input})

    print(result["ask"])
    confirmation = input(">>> ")

    # 二次调用
    result = await graph.ainvoke({"input": user_input, "confirmation": confirmation})
    print(result["order_status"])

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())