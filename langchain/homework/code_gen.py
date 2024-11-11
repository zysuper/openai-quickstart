from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
import gradio as gr


java_template = """你是一位专业的 Java 开发工程师。请根据用户的需求，生成对应的 Java 代码。

用户需求: {requirement}

请生成符合以下要求的代码:
1. 代码应该遵循 Java 编码规范
2. 代码应该包含必要的注释
3. 代码应该具有良好的可读性和可维护性
4. 如果需要,可以包含异常处理

请生成代码:"""

java_prompt = ChatPromptTemplate.from_template(java_template)

python_template = """你是一位专业的 Python 开发工程师。请根据用户的需求，生成对应的 Python 代码。

用户需求: {requirement}

请生成符合以下要求的代码:
1. 代码应该遵循 PEP8 编码规范
2. 代码应该包含必要的注释和文档字符串
3. 代码应该具有良好的可读性和可维护性
4. 如果需要,可以包含异常处理和类型提示

请生成代码:"""

python_prompt = ChatPromptTemplate.from_template(python_template)

openai = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

java_agent = java_prompt | openai | StrOutputParser()
python_agent = python_prompt | openai | StrOutputParser()

chain = (
    {"requirement": RunnablePassthrough()} 
    | RunnableParallel({"java": java_agent, "python": python_agent})
)

def generate_code(requirement) -> tuple[str, str]:
    result = chain.invoke(requirement)
    return result['java'], result['python']

demo = gr.Interface(
        fn=generate_code,
        inputs=gr.Textbox(label="请输入功能需求描述", lines=3),
        outputs=[
            gr.Markdown(label="Java 代码实现", elem_classes="code-output"),
            gr.Markdown(label="Python 代码实现", elem_classes="code-output")
        ],
        title="多语言代码生成器",
        description="输入功能需求描述，自动生成 Java 和 Python 代码实现"
    )

with gr.Blocks() as demo:
    gr.Markdown(value="## 多语言代码生成器")
    input = gr.Textbox(label="请输入功能需求描述", lines=3)
    with gr.Row():
        btn = gr.Button("生成代码", scale=1)
        clear_btn = gr.ClearButton(scale=1)
    with gr.Row():
        gr.Markdown(value="### Java 代码实现")
        gr.Markdown(value="### Python 代码实现")
    with gr.Row():
        output_java = gr.Markdown(label="Java 代码实现", show_label=True, height=600)
        output_python = gr.Markdown(label="Python 代码实现", show_label=True, height=600)

    btn.click(generate_code, inputs=input, outputs=[output_java, output_python])
    clear_btn.click(lambda: None, None, [input, output_java, output_python])


if __name__ == "__main__":
    demo.launch(share=False, server_name="0.0.0.0")




