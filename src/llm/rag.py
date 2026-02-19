from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector import retriever

model = OllamaLLM(model = "llama3.2")

template = """
You are an expert in finding claims, trends, and narratives in the AI field from transcripts from YouTube videos.
Here are some relevant transcripts from those videos: {transcripts}
Here is a question from the user: {question}
"""

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

while True:
    print("\n\n-----------------------------")
    question = input("Ask your question (q to quit): ")
    print("\n\n")
    if question.lower() == "q":
        break

    transcripts = retriever.invoke(question)

    result = chain.invoke({"transcripts": transcripts, "question": question})
    print(result)

