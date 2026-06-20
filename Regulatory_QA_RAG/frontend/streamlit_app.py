import requests
import streamlit as st


BACKEND_URL = "http://backend:8000"


st.set_page_config(
    page_title="RAG Document Assistant",
    page_icon="📄",
    layout="wide",
)

st.title("📄 RAG Document Intelligence Assistant")
st.write(
    "Upload documents, build a FAISS vector index, and ask questions using local LLM + RAG."
)


with st.sidebar:
    st.header("1. Upload Documents")

    uploaded_files = st.file_uploader(
        "Upload PDF or TXT files",
        type=["pdf", "txt"],
        accept_multiple_files=True,
    )

    if st.button("Upload Files"):
        if not uploaded_files:
            st.warning("Please upload at least one file.")
        else:
            files = [
                ("files", (file.name, file.getvalue(), file.type))
                for file in uploaded_files
            ]

            response = requests.post(f"{BACKEND_URL}/upload", files=files)

            if response.status_code == 200:
                st.success("Files uploaded successfully.")
                st.json(response.json())
            else:
                st.error(response.text)

    st.header("2. Build Vector Index")

    if st.button("Build FAISS Index"):
        response = requests.post(f"{BACKEND_URL}/build-index")

        if response.status_code == 200:
            st.success("Vector index built successfully.")
            st.json(response.json())
        else:
            st.error(response.text)

    st.header("Uploaded Documents")

    if st.button("Refresh Document List"):
        response = requests.get(f"{BACKEND_URL}/documents")

        if response.status_code == 200:
            st.json(response.json())
        else:
            st.error(response.text)


st.header("3. Ask Questions")

question = st.text_input(
    "Ask a question about your uploaded documents",
    placeholder="Example: Why is semantic search better than keyword search?",
)

if st.button("Ask"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Retrieving context and generating answer..."):
            response = requests.post(
                f"{BACKEND_URL}/ask",
                json={"question": question},
            )

        if response.status_code == 200:
            result = response.json()

            st.subheader("Answer")
            st.write(result["answer"])

            st.subheader("Retrieved Sources")
            for source in result["sources"]:
                with st.expander(
                    f"{source['file_name']} | Chunk {source['chunk_id']} | Score: {source['similarity_score']}"
                ):
                    st.write(source["preview"])
        else:
            st.error(response.text)