import PyPDF2
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.docstore.document import Document
from groq import Groq
import os
import instructor
from pydantic import BaseModel

class result(BaseModel):
    grade: int
    remarks: str
    strengths: str
    area_of_improvement: str




def build_faiss_index(pdf_paths, output_dir="faiss_index"):
    """
    Build and save a FAISS vector store from a list of PDF paths.

    Args:
        pdf_paths (list): List of paths to PDF files.
        output_dir (str): Directory to save the FAISS index.
    """
    text = ""
    for pdf_path in pdf_paths:
        pdf_reader = PyPDF2.PdfReader(pdf_path)
        for page in pdf_reader.pages:
            text += page.extract_text()

    text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=200, length_function=len)
    chunks = text_splitter.split_text(text)

    docs = [Document(page_content=chunk) for chunk in chunks]
    embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

    faiss_db = FAISS.from_documents(docs, embedding_function)
    faiss_db.save_local(output_dir)


def get_relevant_excerpts(user_question, faiss_db):
    """
    Retrieve the most relevant excerpts from FAISS vector store based on the user's question.

    Args:
        user_question (str): The user's question.
        faiss_db (FAISS): FAISS vector store.

    Returns:
        str: Combined relevant excerpts.
    """
    relevant_docs = faiss_db.similarity_search(user_question, k=3)
    relevant_excerpts = '\n\n------------------------------------------------------\n\n'.join(
        [doc.page_content for doc in relevant_docs]
    )
    return relevant_excerpts


def evaluate_student_submission(client, model, user_question, relevant_excerpts):
    """
    Generate a response to the user's question using a pre-trained model.

    Args:
        client (Groq): Groq client.
        model (str): Pre-trained model name.
        user_question (str): User's question.
        relevant_excerpts (str): Relevant excerpts from speeches.

    Returns:
        str: Response to the user's question.
    """
    system_prompt = '''
    You are an automated evaluator. Review the student’s submission against the assignment instructions, and provide a grade (out of 100) and remarks.

    ### Instructions:
    1. **Review Assignment**: Understand the task, objectives, and guidelines from the assignment description.
    2. **Review Submission**: Assess the student’s submission based on:
    - **Correctness**: Does it meet the requirements and solve the task?
    - **Completeness**: Are all parts addressed?
    - **Clarity**: Is it clear and well-organized?
    - **Quality**: Is it high quality (correct code, well-written)?
    - **Creativity**: (If applicable) Original thinking or approach?
    
    3. **Provide Output**:  
    - **Grade**: Numeric grade out of 100.  
    - **Remarks**: Brief feedback highlighting overall performance.
    - **Strengths**: Brief feedback highlighting strengths.
    - **Area of Improvement**: Brief feedback highlighting areas for improvement.

    '''


    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User Question: {user_question}\n\nStudent Submission:\n\n{relevant_excerpts}"}
        ],
        model=model,
        response_model=result
    )

    # response = chat_completion.choices[0].message.content
    return response


def evaluate_submission(problem, submission_pdf):

    model = 'llama3-8b-8192'
    embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    pdf_paths = [submission_pdf]
    build_faiss_index(pdf_paths)
    # Load FAISS database
    faiss_db = FAISS.load_local("faiss_index", embedding_function, allow_dangerous_deserialization=True)

    # Initialize Groq client
    groq_api_key = os.environ.get('GROQ_API_KEY')
    client = Groq(api_key=groq_api_key)
    # Enable instructor patches for Groq client
    client = instructor.from_groq(client)


    user_question = problem

    if user_question:
        relevant_excerpts = get_relevant_excerpts(user_question, faiss_db)
        response = evaluate_student_submission(client, model, user_question, relevant_excerpts)
        print(response)
        return response

