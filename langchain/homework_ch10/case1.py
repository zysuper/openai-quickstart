from langchain_core.tools import tool
from langchain_core.messages import AIMessage, ToolMessage,HumanMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_experimental.utilities import PythonREPL
from langchain_community.tools import TavilySearchResults
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END

from typing import Annotated, Sequence, TypedDict, Literal
from datetime import datetime
import functools
import operator
import json
import os
import requests
from bs4 import BeautifulSoup

# 定义图中传递的对象，包含消息和发送者信息
class AgentState(TypedDict):
    # 是否打印调试信息
    debug: bool
    # messages 是传递的消息，使用 Annotated 和 Sequence 来标记类型
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # sender 是发送消息的智能体
    sender: str

def debug_print(debug: bool, *args: str) -> None:
    if not debug:
        return
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = " ".join(map(str, args))
    print(f"\033[97m[\033[90m{timestamp}\033[97m]\033[90m {message}\033[0m")

def convert_table_to_markdown(table, debug: bool = False):
    # 提取表头
    headers = []
    for th in table.find_all('th'):
        headers.append(th.text.strip())
        
    # 提取数据行
    rows = []
    for tr in table.find_all('tr')[1:]:  # 跳过表头行
        row = []
        for td in tr.find_all('td'):
            row.append(td.text.strip())
        if row:  # 只添加非空行
            rows.append(row)
            
    # 生成markdown表格
    markdown = "| " + " | ".join(headers) + " |\n"
    markdown += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    
    for row in rows:
        markdown += "| " + " | ".join(row) + " |\n"
        
    debug_print(debug, f"提取到表格数据:\n{markdown}")
    return markdown
  
def create_scraper_tool(debug: bool = False):
    @tool
    def scraper(
        url: Annotated[str, "The url of the website to scrape."]
    ):
        """Use this to scrape data from a website. If you want to see the output of a value,
        you should print it out with `print(...)`. This is visible to the user."""
        bs = BeautifulSoup(requests.get(url).text, "html.parser")
        
        text = ""
        # 查找页面中的表格
        tables = bs.find_all('table')
        if not tables:
            return "未找到表格数据"

        for table in tables:
            markdown = convert_table_to_markdown(table, debug)
            text += markdown + "\n"
        
        return text
    return scraper

def create_python_repl_tool(debug: bool = False):
    repl = PythonREPL()

    @tool
    def python_repl(
        code: Annotated[str, "The python code to execute to generate your chart."],
    ):
        """Use this to execute python code. If you want to see the output of a value,
        you should print it out with `print(...)`. This is visible to the user."""
        try:
            result = repl.run(code)
            debug_print(debug, f"Python REPL executed code: {code}")
            debug_print(debug, f"Python REPL result: {result}")
        except BaseException as e:
            debug_print(debug, f"Python REPL error: {repr(e)}")
            return f"Failed to execute. Error: {repr(e)}"


        return f"Successfully executed:\n```python\n{code}\n```\n"

    return python_repl

def agent_node(state, agent, name, debug: bool = False):
    """
    创建一个智能体节点
    """
    # 修正名称格式，移除空格并确保只包含合法字符
    name = name.replace(" ", "_").replace("-", "_")  

    # 调用智能体
    result = agent.invoke(state)
    
    debug_print(debug, f"Agent {name} invoked with state: {state}")
    debug_print(debug, f"Agent {name} returned: {result}")

    if isinstance(result, ToolMessage):
        pass
    else:
        result = AIMessage(**result.dict(exclude={"type", "name"}), name=name)

    return {
        "messages": [result],
        "sender": name,
    }
    
def create_agent(llm, tools, tool_message: str, custom_notice: str=""):
    """创建一个智能体。"""
    # 定义智能体的提示模板，包含系统消息和工具信息
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful AI assistant, collaborating with other assistants."
                " Use the provided tools to progress towards answering the question."
                " If you are unable to fully answer, that's OK, another assistant with different tools "
                " will help where you left off. Execute what you can to make progress."
                " If you or any of the other assistants have the final answer or deliverable,"
                " prefix your response with FINAL ANSWER so the team knows to stop."
                "\n{custom_notice}\n"
                " You have access to the following tools: {tool_names}.\n{tool_message}\n\n",
            ),
            MessagesPlaceholder(variable_name="messages"),  # 用于替换的消息占位符

        ]
    )

    # 将系统消息部分和工具名称插入到提示模板中
    prompt = prompt.partial(tool_message=tool_message, custom_notice=custom_notice)
    prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
      
    # 将提示模板与语言模型和工具绑定
    return prompt | llm.bind_tools(tools)
    
def router(state) -> Literal["call_tool", "__end__", "continue"]:
    messages = state["messages"]  # 获取当前状态中的消息列表
    last_message = messages[-1]  # 获取最新的一条消息
    
    # 如果最新消息包含工具调用，则返回 "call_tool"，指示执行工具
    if last_message.tool_calls:
        return "call_tool"
    
    # 如果最新消息中包含 "FINAL ANSWER"，表示任务已完成，返回 "__end__" 结束工作流
    if "FINAL ANSWER" in last_message.content:
        return "__end__"
    
    # 如果既没有工具调用也没有完成任务，继续流程，返回 "continue"
    return "continue"

def run_multi_agent_test(model_factory, debug: bool = False):
    # 1. llms
    research_llm = model_factory()
    chart_llm = model_factory()
    
    # 2. tools
    tavily_tool = TavilySearchResults(max_results=5)
    python_repl_tool = create_python_repl_tool(debug)
    scraper_tool = create_scraper_tool(debug)

    # 3. agents & prompt
    research_agent = create_agent(
        research_llm,  # 使用 research_llm 作为研究智能体的语言模型
        [tavily_tool, scraper_tool],  # 研究智能体使用 Tavily 搜索工具
        tool_message=(
            "Before using the search engine and scraper, carefully think through and clarify the query."
            " Then, conduct a single search that addresses all aspects of the query in one go",
        ),
        custom_notice=(
            "Notice:\n"
            "Only gather and organize information. Do not generate code or give final conclusions, leave that for other assistants."
        ),
    )
    chart_agent = create_agent(
        chart_llm,  # 使用 chart_llm 作为图表生成器智能体的语言模型
        [python_repl_tool],  # 图表生成器智能体使用 Python REPL 工具
        tool_message="Create clear and user-friendly charts based on the provided data.",  # 系统消息，指导智能体如何生成图表
        custom_notice="Notice:\n"
            "If you have completed all tasks, respond with FINAL ANSWER.",
    )
    
    # nodes
    research_node = functools.partial(agent_node, agent=research_agent, name="Researcher", debug=debug)
    chart_node = functools.partial(agent_node, agent=chart_agent, name="Chart_Generator", debug=debug)
    tool_node = ToolNode(tools=[tavily_tool, python_repl_tool, scraper_tool], name="call_tool")

    # graph build
    workflow = StateGraph(AgentState)

    # add nodes
    workflow.add_node("Researcher", research_node)
    workflow.add_node("Chart_Generator", chart_node)
    workflow.add_node("call_tool", tool_node)

    # add edges
    workflow.add_edge(START, "Researcher")
    workflow.add_conditional_edges(
        "Researcher", 
        router,
        {
            "call_tool": "call_tool",
            "__end__": END,
            "continue": "Chart_Generator",
        }
    )
    workflow.add_conditional_edges(
        "Chart_Generator",
        router,
        {
            "__end__": END,
            "continue": "Researcher",
            "call_tool": "call_tool",
        }
    )
    workflow.add_conditional_edges(
        "call_tool", 
        lambda x: x["sender"], 
        {
            "Researcher": "Researcher",
            "Chart_Generator": "Chart_Generator",
        }
    )
    
    graph = workflow.compile()
    
    print("\n=== Graph Structure ===")
    print(graph.get_graph().draw_ascii())

    events = graph.stream(
        {
            "messages": [
                HumanMessage(
                    content="Obtain the GDP of the United States from 2000 to 2020, "
                        "and then plot a line chart with Python. End the task after generating the chart. "
                        "The recommended search website is https://www.statista.com."
                )
            ]
        },
        {"recursion_limit": 20},
        stream_mode="values",
    )
    
    event_list = []
    for event in events:
        if "messages" in event:
            last_message = event["messages"][-1]
            event_list.append(last_message.pretty_repr())  # 打印消息内容
            last_message.pretty_print()  # 打印消息内容
    return event_list
    

def main():
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "Multi-agent Collaboration"
    
    # 需要测试的模型
    models = {
        "gpt-4o-mini": lambda: ChatOpenAI(model="gpt-4o-mini"),
        "gpt-3.5-turbo": lambda: ChatOpenAI(model="gpt-3.5-turbo"),
        "deepseek-chat": lambda: ChatOpenAI(model="deepseek-chat", base_url="https://api.deepseek.com/v1", api_key=os.getenv("DEEPSEEK_API_KEY")),
        "qwen2.5:14b": lambda: ChatOllama(model="qwen2.5:14b", base_url="http://localhost:11434")
    }
    
    result_map = {model_name: run_multi_agent_test(model_factory) for model_name, model_factory in models.items()}

    # 将结果保存到文件
    with open('model_results.json', 'w', encoding='utf-8') as f:
        json.dump(result_map, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
    