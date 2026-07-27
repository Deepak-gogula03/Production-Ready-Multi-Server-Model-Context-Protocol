from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage

from dotenv import load_dotenv
load_dotenv()

import asyncio
import os
import sys

MATH_SYSTEM_PROMPT = SystemMessage(
    content=(
        "You have access to math tools: add, subtract, multiply, divide. "
        "For multi-step problems, call ONE tool per turn and wait for its "
        "integer result before calling the next tool. Never pass a tool call "
        "as an argument to another tool — only pass plain integers."
    )
)

WEATHER_SYSTEM_PROMPT = SystemMessage(
    content=(
        "You have access to a get_weather tool. Always use it to answer "
        "weather questions and report the tool result to the user."
    )
)


async def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    client = MultiServerMCPClient(
        {
            "math": {
                "command": sys.executable,
                "args": [os.path.join(base_dir, "mathserver.py")],
                "transport": "stdio",
            },
            "weather": {
                "url": "http://localhost:8000/mcp",
                "transport": "streamable-http",
            },
        }
    )

    tools = await client.get_tools()
    math_tools = [t for t in tools if t.name in ("add", "subtract", "multiply", "divide")]
    weather_tools = [t for t in tools if t.name == "get_weather"]

    model = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    math_agent = create_react_agent(
        model, math_tools, prompt=MATH_SYSTEM_PROMPT, debug=True
    )
    weather_agent = create_react_agent(
        model, weather_tools, prompt=WEATHER_SYSTEM_PROMPT, debug=True
    )

    math_response = await math_agent.ainvoke(
        {"messages": [{"role": "user", "content": "What is (3+5)*2?"}]}
    )
    print("Math Response:", math_response["messages"][-1].content)

    weather_response = await weather_agent.ainvoke(
        {"messages": [{"role": "user", "content": "What is the weather in Tokyo?"}]}
    )
    print("Weather Response:", weather_response["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
