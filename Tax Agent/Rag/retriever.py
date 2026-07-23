"""
retriever.py

Creates and returns a FAISS retriever
using NVIDIA Embeddings.
"""

from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFDirectoryLoader,
)

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)

from langchain_community.vectorstores import FAISS

from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

from dotenv import load_dotenv

import os

load_dotenv()

DATA_PATH = "Data"

VECTOR_DB_PATH = "vectorstore/faiss_index"

EMBEDDING_MODEL = "nvidia/nv-embedqa-e5-v5"

api_key = os.getenv("NVIDIA_API_KEY")


def load_documents():

    loader = PyPDFDirectoryLoader(DATA_PATH)

    documents = loader.load()

    return documents


def split_documents(documents):

    splitter = RecursiveCharacterTextSplitter(

        chunk_size=1000,

        chunk_overlap=200,

        separators=[
            "\n\n",
            "\n",
            ". ",
            " "
        ]
    )

    return splitter.split_documents(documents)


def get_embeddings():

    return NVIDIAEmbeddings(

        model=EMBEDDING_MODEL,

        api_key=api_key
    )


def create_vector_store():

    documents = load_documents()

    chunks = split_documents(documents)

    embeddings = get_embeddings()

    vectorstore = FAISS.from_documents(

        chunks,

        embeddings

    )

    Path("vectorstore").mkdir(

        exist_ok=True

    )

    vectorstore.save_local(

        VECTOR_DB_PATH

    )

    return vectorstore


def load_vector_store():

    embeddings = get_embeddings()

    return FAISS.load_local(

        VECTOR_DB_PATH,

        embeddings,

        allow_dangerous_deserialization=True

    )


def get_retriever():

    if Path(VECTOR_DB_PATH).exists():

        vectorstore = load_vector_store()

    else:

        vectorstore = create_vector_store()

    retriever = vectorstore.as_retriever(

        search_type="similarity",

        search_kwargs={

            "k": 4

        }

    )

    return retriever