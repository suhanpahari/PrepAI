# prepros.py
from llm_add import llm
from langchain_core.prompts import PromptTemplate

# Function to generate precise disaster-related information
def generate_disaster_response(question, response):
    template = '''
    you are a question helper, you have to check all the response with the answer
    so, if there is a completly wrong answer of a question reply correct answer starting with 0
    if correct start with 1 no need to to reply. if partially correct start with 0.5 and give the modify 
    reply

    question: {question}
    response: {response}

    max word limit 500.
    '''
    
    # Create the prompt
    prompt = PromptTemplate.from_template(template)
    
    # Prepare the input for the LLM
    chain = prompt | llm
    
    # Invoke the LLM with the input
    response = chain.invoke(input={"question": question, "response": response})
    
    return response.content