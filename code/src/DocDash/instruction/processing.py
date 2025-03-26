import os
import re
import pandas as pd
from langchain.document_loaders import PyPDFLoader, CSVLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI


class RegulatoryInstructionProcessor:
    def __init__(self, model_name="gpt-4", embedding_model="text-embedding-ada-002"):
        """Initialize the processor with specified LLM and embedding models."""
        self.llm = OpenAI(model_name=model_name)
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        self.vector_db = None

    def load_documents(self, document_path):
        """Load documents from various formats."""
        documents = []
        ext = os.path.splitext(document_path)[1].lower()

        if ext == '.pdf':
            loader = PyPDFLoader(document_path)
            documents = loader.load()
        elif ext == '.csv':
            loader = CSVLoader(document_path)
            documents = loader.load()
        elif ext in ['.txt', '.md']:
            loader = TextLoader(document_path)
            documents = loader.load()
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        return documents

    def process_documents(self, document_paths):
        """Process multiple documents and create a vector store."""
        all_documents = []
        for path in document_paths:
            documents = self.load_documents(path)
            all_documents.extend(documents)

        chunks = self.text_splitter.split_documents(all_documents)
        self.vector_db = Chroma.from_documents(chunks, self.embeddings)

    def extract_validation_requirements(self):
        """Extract data validation requirements from processed documents."""
        if not self.vector_db:
            raise ValueError("No documents have been processed yet.")

        retriever = self.vector_db.as_retriever(search_kwargs={"k": 5})
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever
        )

        # Extract allowable values
        allowable_values_query = """
        Extract all mentions of allowable values, valid ranges, or permitted values for data elements.
        Format the output as a JSON object with the field name as key and the allowable values as values.
        """
        allowable_values = qa_chain.run(allowable_values_query)

        # Extract required fields
        required_fields_query = """
        Identify all mandatory fields or required elements mentioned in the regulatory documents.
        Format the output as a JSON array of field names.
        """
        required_fields = qa_chain.run(required_fields_query)

        # Extract cross-field validation rules
        cross_validation_query = """
        Extract all rules that describe relationships or dependencies between different data elements.
        Format the output as a JSON array of objects, each containing the fields involved and the rule description.
        """
        cross_validations = qa_chain.run(cross_validation_query)

        # Extract data type constraints
        data_type_query = """
        Identify all data type constraints for each field (e.g., numeric, date, string, etc.).
        Format the output as a JSON object with field names as keys and data types as values.
        """
        data_types = qa_chain.run(data_type_query)

        return {
            "allowable_values": allowable_values,
            "required_fields": required_fields,
            "cross_validations": cross_validations,
            "data_types": data_types
        }

    def refine_requirements(self, extracted_requirements):
        """Use LLM to refine and standardize the extracted requirements."""
        refinement_prompt = f"""
        Given the following extracted data validation requirements, please:
        1. Standardize the format of all rules
        2. Resolve any ambiguities or contradictions
        3. Ensure all field names are consistent
        4. Convert descriptive rules into executable logic where possible

        Requirements to refine:
        {extracted_requirements}

        Return the refined requirements in a structured JSON format.
        """

        refined_requirements = self.llm(refinement_prompt)
        return refined_requirements
