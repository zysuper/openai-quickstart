from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


def load_and_split_text(file_path: str) -> list[str]:
    """
    从文件读取文本并按照分隔符拆分成块
    
    Args:
        file_path: 文本文件路径
        
    Returns:
        拆分后的文本块列表
    """
    # 从文件读取文本
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    # 直接用 \n\n 分割文本
    # 注意：这里没有使用 CharacterTextSplitter，因为 CharacterTextSplitter 会基于字符长度分割文本，而这里我们希望严格基于 \n\n 分割文本
    # 文本切分的粒度的准确性，对于问题的召回率至关重要
    texts = text.split("\n\n")

    # 过滤掉空字符串
    return [t for t in texts if t]

def test_recall(vs: Chroma):
    questions = [
     "UCP600第38条h款关于第一受益人的权利是什么？", 
     "UCP600第35条是如何规定开证行或保兑行对遗失单据的责任的？",
     "开证行以\"B/L doesn't show port of loading as required under L/C field 44E.\"为由拒付，这个理由站得住脚吗？"
    ]
    print(f"【开始测试 rag 召回率】：\n")
    retriever = vs.as_retriever()
    for question in questions:
        results = retriever.invoke(question)
        print(f"问题: \n{question}")
        print(f"召回的文档: \n{results[0].page_content}")
        print("-" * 100)
    print(f"【结束测试 rag 召回率】：\n")


if __name__ == "__main__":
    # 调用函数拆分文本
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"当前目录路径: {current_dir}")
    texts = load_and_split_text(f"{current_dir}/信用证FAQ.txt")

    print(f"文本块数: {len(texts)}")
    #print(texts[0])

    # 创建向量存储
    vectorstore = Chroma.from_texts(texts, OpenAIEmbeddings(), collection_name="credit-letter-faq")

    test_recall(vectorstore)
    
    # 加载 prompt
    prompt = hub.pull("mrparrot/counterfactual-prompt")
    #print(f"prompt: \n{prompt}")
    
    # 创建召回器
    retriever = vectorstore.as_retriever()
    setup_and_retrieval = RunnableParallel({"context": retriever, "question": RunnablePassthrough()})

    # 创建模型
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

    # 创建 output parser
    output_parser = StrOutputParser()

    chain = setup_and_retrieval | prompt | model | output_parser

    result = chain.invoke("UCP600第38条h款关于第一受益人的权利是什么？")
    
    print("-" * 100)
    print(f"问题: \nUCP600第38条h款关于第一受益人的权利是什么？\n")
    print(f"回答: \n{result}")

