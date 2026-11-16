"""Chunk a transcript, embed it, and answer questions from those chunks only."""

import asyncio
import uuid

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains.retrieval import create_retrieval_chain

from sonar_mind.config import GEMINI_EMBED_MODEL, PERSIST_DIRECTORY, get_api_key
from sonar_mind.llm import make_llm
from sonar_mind import state

GROUNDED_PROMPT = ChatPromptTemplate.from_template(
    """You are Sonar Mind, an educational assistant.
Answer the question using only the lecture excerpts in the context.
If the context does not contain the answer, say that the lecture does not cover it.
Do not add facts from outside the lecture.
Write a clear answer a student can revise from.

Context:
{context}

Question:
{input}
"""
)


def chunk_transcript(text: str, chunk_size: int = 800, overlap_size: int = 150):
    document = [Document(page_content=text)]
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap_size,
    )
    chunks = splitter.split_documents(documents=document)
    print(f"File split into {len(chunks)} chunks.")
    return chunks


def _ensure_event_loop():
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())


def create_vector_db(text_chunks, collection_name: str | None = None):
    if not text_chunks:
        raise ValueError("No transcript chunks to index.")
    _ensure_event_loop()
    collection_name = collection_name or f"lecture-{uuid.uuid4().hex[:8]}"
    embeddings = GoogleGenerativeAIEmbeddings(
        model=GEMINI_EMBED_MODEL,
        google_api_key=get_api_key(),
    )
    vector_db = Chroma.from_documents(
        documents=text_chunks,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory=PERSIST_DIRECTORY,
    )
    print(f"Vector DB created with collection_name: {collection_name}")
    return vector_db


def setup_rag_chain(vector_db):
    if not vector_db:
        raise ValueError("Vector DB not initialized.")
    llm = make_llm(temperature=0.1)
    document_chain = create_stuff_documents_chain(llm, GROUNDED_PROMPT)
    retriever = vector_db.as_retriever(search_kwargs={"k": 4})
    return create_retrieval_chain(retriever, document_chain)


def handle_indexing_request(transcript_text: str) -> str:
    if not transcript_text or not transcript_text.strip():
        return "Transcript is empty. Transcribe audio or paste lecture text first."
    try:
        chunks = chunk_transcript(transcript_text)
        state.vector_db = create_vector_db(chunks)
        state.rag_chain = setup_rag_chain(state.vector_db)
        return f"Indexing complete. {len(chunks)} chunks indexed."
    except Exception as exc:
        return f"Indexing failed: {exc}"


def query(chain, question: str) -> str:
    if not chain:
        raise RuntimeError("RAG chain not initialized.")
    result = chain.invoke({"input": question})
    if isinstance(result, dict):
        return str(result.get("answer") or result)
    return str(result)


def answer_query_using_rag(user_query: str) -> str:
    if not state.rag_chain:
        return "Please index the transcript first."
    try:
        return query(state.rag_chain, user_query)
    except Exception as exc:
        return f"Error: {exc}"


def handle_query_request(user_query: str) -> str:
    if not user_query or not user_query.strip():
        return "Please enter a question about the lecture."
    return answer_query_using_rag(user_query.strip())
