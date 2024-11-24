import os
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from typing import TypedDict, Annotated
from langgraph.graph import add_messages
from typing_extensions import TypedDict
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
import asyncio
from rich.console import Console
from rich.markdown import Markdown

model_name = "llama3.1:8b-instruct-q8_0"
ollama_url = "http://localhost:11434/v1"
deepseek_url = "https://api.deepseek.com/v1"
MAX_ROUND = 6

console = Console()

def display(md: Markdown):
    console.print(md)

def writer_agent(url=ollama_url):
    writer_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a versatile writing assistant who can generate any type of content including code, stories and articles."
                " Create high-quality content based on user requests while adapting style and format as needed."
                " When revising, incorporate feedback and build upon previous versions to improve the writing."
                " Notice: Focus on the writing task itself!!! Don't spend time responding to user suggestions and improvements."
            ),
            (
                "human",
                "Please write content according to the following requirements: {write_task}"
            ),
            (
                "ai",
                "The previous content I wrote: {last_content}"
            ),
            (
                "human",
                "Here are the suggestions for improvement from the last review: {last_reflection}"
            ),
        ]
    )
    
    writer = writer_prompt | ChatOpenAI(
        model=model_name,
        max_tokens=8192,
        temperature=1.2,
        base_url=ollama_url,
    )

    return writer
    
def reflection_agent(url=ollama_url):
    reflection_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a content reviewer. Review submissions and provide specific constructive critique and improvement suggestions."
                " For code: check correctness, readability and best practices."
                " For articles: evaluate structure, flow, and style."
                " For documents: assess completeness, logic, and organization."
                " Notice: Do not rewrite the content yourself, focus only on giving constructive feedback!!!"
            ),
            MessagesPlaceholder(variable_name="messages"),  
        ]
    )

    reflect = reflection_prompt | ChatOpenAI(
        model=model_name,
        max_tokens=8192,
        temperature=0.2,
        base_url=ollama_url,
    ) 

    return reflect
    
class State(TypedDict):
    messages: Annotated[list, add_messages]

def create_generation_node():
    writer = writer_agent()
    async def generation_node(state: State, config: dict) -> State:
        write_task = state["messages"][0].content
        if len(state["messages"]) > 1:
            last_reflection = state["messages"][-1].content
            last_content = state["messages"][-2].content
        else:
            last_reflection = "No suggestions for improvement yet. This is the first writing attempt."
            last_content = "This is the first writing attempt. No previous content exists."
        return {"messages": [await writer.ainvoke({
            "write_task": write_task,
            "last_content": last_content,
            "last_reflection": last_reflection,
        })]}
    return generation_node

def create_reflection_node():
    reflect = reflection_agent()
    async def reflection_node(state: State) -> State:
        cls_map = {"ai": HumanMessage, "human": AIMessage}

        # 如果有多轮对话，则将前一轮的对话内容做 reflect 处理
        if len(state['messages']) > 1:
            translated = [state['messages'][0]] + [
                cls_map[msg.type](content=msg.content) for msg in state['messages'][1:]
            ]
        else:
            translated = [state['messages'][0]]
    
        res = await reflect.ainvoke(translated)

        return {"messages": [HumanMessage(content=res.content)]}
    return reflection_node

def should_continue(state: State):
    if len(state["messages"]) > MAX_ROUND:
        return END  # 达到条件时，流程结束
    return "reflect"  # 否则继续进入反思节点

def make_graph():
    memory = MemorySaver()

    builder = StateGraph(State)
    generation_node = create_generation_node()
    reflection_node = create_reflection_node()

    builder.add_node("writer", generation_node)
    builder.add_node("reflect", reflection_node)

    builder.add_edge(START, "writer")

    builder.add_conditional_edges(
        "writer",
        should_continue,
        {
            END: END,
            "reflect": "reflect",
        }
    )
    
    builder.add_edge("reflect", "writer")

    graph = builder.compile(checkpointer=memory)

    print(graph.get_graph().draw_ascii())

    return graph

def track_steps(func):
    step_counter = {'count': 0}  # 用于记录调用次数
    
    def wrapper(event, *args, **kwargs):
        # 增加调用次数
        step_counter['count'] += 1
        # 在函数调用之前打印 step
        display(Markdown(f"## Round {step_counter['count']}"))
        # 调用原始函数
        return func(event, *args, **kwargs)
    
    return wrapper

@track_steps
def pretty_print_event_markdown(event):
    # 如果是生成写作部分
    if 'writer' in event:
        generate_md = "#### 写作生成:\n"
        for message in event['writer']['messages']:
            generate_md += f"- {message.content}\n"
        display(Markdown(generate_md))
    
    # 如果是反思评论部分
    if 'reflect' in event:
        reflect_md = "#### 评论反思:\n"
        for message in event['reflect']['messages']:
            reflect_md += f"- {message.content}\n"
        display(Markdown(reflect_md))
    
async def main():
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "Reflection_story"

    graph = make_graph()
    
    config =  {"configurable": {"thread_id": "1"}}
    
    # 写故事.
    async for event in graph.astream(
        {
            "messages": [HumanMessage(content="参考西游记的故事，用中文编写一个南游记慧能大师传法的故事。")],
        },
        config,
    ):
        pretty_print_event_markdown(event)
    
    print("-" * 200)
    
    # 写代码.
    # async for event in graph.astream(
    #     {"messages": [HumanMessage(content="用 python 语言编写一个贪吃蛇的游戏代码。")]},
    #     {"configurable": {"thread_id": "2"}},
    # ):
    #     pretty_print_event_markdown(event)

if __name__ == "__main__":
    asyncio.run(main())

