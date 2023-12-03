import streamlit as st
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import UnstructuredPDFLoader
from io import StringIO
import os

# Set OPENAI_API_KEY as an environment variable
openai_api_key = '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'
os.environ["OPENAI_API_KEY"] = openai_api_key

llm = ChatOpenAI(temperature=0,max_tokens=1000,model_name="gpt-3.5-turbo")

# chat UI title
st.title("Chat with your documents using Langchain")

# file uploader in the sidebar in the left
with st.sidebar:
    uploaded_files = st.file_uploader("load pdf files", accept_multiple_files=True, type="pdf")

#check if files are uploaded
    if uploaded_files:
        #Print the number of files to console
        print(f"Number of files uploaded: {len(uploaded_files)}")

        # Load the data and perform preprocessing only if it hasn't been loaded before
        if "processed_data" not in st.session_state:
            # Load the data from uploaded files
            documents = []

            for uploaded_file in uploaded_files:
                # Get the full file path of the uploaded file
                file_path = os.path.join(os.getcwd(), uploaded_file.name)

                # Save the uploaded file to disk
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())

                #Use UnstructuredPDFLoader to load the PDF file
                loader = UnstructuredPDFLoader(file_path)
                loaded_documents = loader.load()
                print(f"Number of files uploaded: {len(loaded_documents)}")

                # Extend the main documents list with the loaded documents
                documents.extend(loaded_documents)

            # Chunk the data, create embeddings, and save in vectorstore
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
            document_chunks = text_splitter.split_documents(documents)

            embeddings = OpenAIEmbeddings()
            vectorstore = Chroma.from_documents(document_chunks, embeddings)

            # Store the processed data in session state for reuse
            st.session_state.processed_data = {
                 "document_chunks": document_chunks,
                "vectorstore": vectorstore,
            }

            #print the total number of chunks to console
            print(f"Number of totak chunks: {len(document_chunks)}")
        else:
            # If the processed data is already available, retrieve it from session state
            document_chunks = st.session_state.processed_data["document_chunks"]
            vectorstore = st.session_state.processed_data["vectorstore"]

        # Initialize Langchain's QA Chain with the vectorstore
        qa = ConversationalRetrievalChain.from_llm(llm, vectorstore.as_retriever())

        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
             with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Accept user input
        if prompt := st.chat_input("Ask your questions?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
               st.markdown(prompt)

            # Query the assistant using the latest chat history
            result = qa({"question": prompt, "chat_history": [(message["role"], message["content"]) for message in st.session_state.messages]})

            # Display assistant response in chat message container
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                full_response = result["answer"]
                message_placeholder.markdown(full_response + "|")
            message_placeholder.markdown(full_response)
            # print(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

    else:
        st.write('Please upload your PDF files.')