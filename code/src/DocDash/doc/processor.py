import os
import re
import email
import pandas as pd
from langchain.document_loaders import PyPDFLoader, TextLoader, UnstructuredEmailLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate


class DocumentProcessor:
    def __init__(self, model_name="gpt-4", embedding_model="text-embedding-ada-002"):
        """Initialize the document processor with specified LLM and embedding models."""
        self.llm = OpenAI(model_name=model_name)
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        self.vector_db = None

    def process_email(self, email_path):
        """Process an email file and extract key information."""
        # Load the email
        loader = UnstructuredEmailLoader(email_path)
        documents = loader.load()

        # Parse the email content
        with open(email_path, 'r', errors='ignore') as f:
            msg = email.message_from_string(f.read())

        # Extract metadata
        metadata = {
            "subject": msg.get("subject", ""),
            "from": msg.get("from", ""),
            "to": msg.get("to", ""),
            "date": msg.get("date", ""),
            "message_id": msg.get("message-id", "")
        }

        # Extract attachments if any
        attachments = []
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue

            filename = part.get_filename()
            if filename:
                # Save the attachment to a temporary file
                attachment_path = os.path.join("/tmp", filename)
                with open(attachment_path, 'wb') as f:
                    f.write(part.get_payload(decode=True))
                attachments.append(attachment_path)

        # Get the email body
        body = ""
        if documents:
            body = documents[0].page_content

        return {
            "metadata": metadata,
            "body": body,
            "attachments": attachments
        }

    def classify_document(self, document_content, document_path=None):
        """Classify the document type and identify key information."""
        # Define classification prompt
        classification_prompt = PromptTemplate(
            input_variables=["document_content", "document_name"],
            template="""
            Analyze the following document content and classify it according to these criteria:

            Document Content:
            {document_content}

            Document Name: {document_name}

            Please classify this document and extract key information by answering these questions:
            1. What type of document is this? (e.g., regulatory filing, financial report, compliance document, etc.)
            2. What is the primary subject or purpose of this document?
            3. Are there any specific regulatory frameworks mentioned? (e.g., GDPR, HIPAA, Basel III, etc.)
            4. What departments or roles would typically be interested in this document?
            5. What is the priority level (High, Medium, Low) for processing this document?
            6. Are there any deadlines or time-sensitive information mentioned?
            7. What key entities (organizations, people, regulations) are mentioned?

            Return your classification in JSON format.
            """
        )

        document_name = os.path.basename(document_path) if document_path else "Unknown"

        # Truncate document content if too long
        max_content_length = 4000  # Limit to avoid token limits
        truncated_content = document_content[:max_content_length]
        if len(document_content) > max_content_length:
            truncated_content += "... [content truncated]"

        # Create and run the classification chain
        classification_chain = LLMChain(llm=self.llm, prompt=classification_prompt)
        classification_result = classification_chain.run(
            document_content=truncated_content,
            document_name=document_name
        )

        # Try to parse as JSON, but fallback to raw text if that fails
        try:
            import json
            # Handle case where LLM might wrap JSON in markdown code blocks
            if "```json" in classification_result:
                json_str = classification_result.split("```json")[1].split("```")[0].strip()
                classification_json = json.loads(json_str)
            else:
                classification_json = json.loads(classification_result)
            return classification_json
        except:
            return {"raw_classification": classification_result}

    def extract_data_elements(self, document_content):
        """Extract structured data elements from unstructured document content."""
        extraction_prompt = PromptTemplate(
            input_variables=["document_content"],
            template="""
            Extract all data elements and their values from the following document content.
            Focus on identifying:
            1. Numeric data fields and their values
            2. Dates and time periods
            3. Categories and classifications
            4. Named entities (people, organizations, locations)
            5. Any field-value pairs that appear to be structured data

            Document Content:
            {document_content}

            Return the extracted data elements in JSON format, with field names as keys and the extracted values.
            For each field, include:
            - The field name
            - The extracted value
            - The data type (string, number, date, boolean, etc.)
            - The confidence level of the extraction (high, medium, low)
            """
        )

        # Truncate document content if too long
        max_content_length = 4000  # Limit to avoid token limits
        truncated_content = document_content[:max_content_length]
        if len(document_content) > max_content_length:
            truncated_content += "... [content truncated]"

        # Create and run the extraction chain
        extraction_chain = LLMChain(llm=self.llm, prompt=extraction_prompt)
        extraction_result = extraction_chain.run(document_content=truncated_content)

        # Try to parse as JSON, but fallback to raw text if that fails
        try:
            import json
            # Handle case where LLM might wrap JSON in markdown code blocks
            if "```json" in extraction_result:
                json_str = extraction_result.split("```json")[1].split("```")[0].strip()
                extraction_json = json.loads(json_str)
            else:
                extraction_json = json.loads(extraction_result)
            return extraction_json
        except:
            return {"raw_extraction": extraction_result}

    def route_document(self, classification, content_summary):
        """Determine the appropriate routing for a document based on its classification."""
        routing_prompt = PromptTemplate(
            input_variables=["classification", "content_summary"],
            template="""
            Based on the following document classification and content summary, determine the optimal routing for this document.

            Document Classification:
            {classification}

            Content Summary:
            {content_summary}

            Please specify:
            1. The primary department or team this should be routed to
            2. Any secondary departments that should be notified
            3. The specific action required (review, approval, processing, etc.)
            4. The recommended priority (High, Medium, Low)
            5. Any specific individuals or roles that should handle this (if identifiable)
            6. Whether this document requires validation against regulatory requirements

            Return your routing recommendation in JSON format.
            """
        )

        # Create and run the routing chain
        routing_chain = LLMChain(llm=self.llm, prompt=routing_prompt)
        routing_result = routing_chain.run(
            classification=str(classification),
            content_summary=str(content_summary)
        )

        # Try to parse as JSON, but fallback to raw text if that fails
        try:
            import json
            # Handle case where LLM might wrap JSON in markdown code blocks
            if "```json" in routing_result:
                json_str = routing_result.split("```json")[1].split("```")[0].strip()
                routing_json = json.loads(json_str)
            else:
                routing_json = json.loads(routing_result)
            return routing_json
        except:
            return {"raw_routing": routing_result}

    def extract_validation_requirements(self, document_content):
        """Extract validation requirements from regulatory or compliance documents."""
        validation_prompt = PromptTemplate(
            input_variables=["document_content"],
            template="""
            Extract all data validation requirements from the following document content.
            Focus on identifying:
            1. Data quality rules
            2. Required fields and mandatory information
            3. Allowed values or value ranges
            4. Cross-field validation rules or dependencies
            5. Format and structure requirements
            6. Reporting thresholds or limits

            Document Content:
            {document_content}

            Return the extracted validation requirements in JSON format, with each requirement containing:
            - A unique identifier
            - The field or data element it applies to
            - The validation rule in clear language
            - The severity of non-compliance (Critical, High, Medium, Low)
            """
        )

        # Truncate document content if too long
        max_content_length = 4000  # Limit to avoid token limits
        truncated_content = document_content[:max_content_length]
        if len(document_content) > max_content_length:
            truncated_content += "... [content truncated]"

        # Create and run the validation extraction chain
        validation_chain = LLMChain(llm=self.llm, prompt=validation_prompt)
        validation_result = validation_chain.run(document_content=truncated_content)

        # Try to parse as JSON, but fallback to raw text if that fails
        try:
            import json
            # Handle case where LLM might wrap JSON in markdown code blocks
            if "```json" in validation_result:
                json_str = validation_result.split("```json")[1].split("```")[0].strip()
                validation_json = json.loads(json_str)
            else:
                validation_json = json.loads(validation_result)
            return validation_json
        except:
            return {"raw_validation": validation_result}

    def process_document_batch(self, document_paths):
        """Process a batch of documents for triage and routing."""
        results = []

        for path in document_paths:
            try:
                # Determine document type and load it
                ext = os.path.splitext(path)[1].lower()
                content = ""

                if ext == ".pdf":
                    loader = PyPDFLoader(path)
                    documents = loader.load()
                    content = "\n".join([doc.page_content for doc in documents])
                elif ext in [".txt", ".md", ".csv"]:
                    loader = TextLoader(path)
                    documents = loader.load()
                    content = documents[0].page_content if documents else ""
                elif ext in [".eml", ".msg"]:
                    email_data = self.process_email(path)
                    content = email_data["body"]
                    # Handle email-specific processing
                    classification = self.classify_document(content, path)
                    data_elements = self.extract_data_elements(content)
                    validation_requirements = None

                    # If document appears to be regulatory or compliance-related, extract validation requirements
                    if classification.get("type", "").lower() in ["regulatory", "compliance", "policy", "procedure"]:
                        validation_requirements = self.extract_validation_requirements(content)

                    # Determine routing
                    content_summary = {
                        "elements": data_elements,
                        "text_sample": content[:500] + "..." if len(content) > 500 else content
                    }
                    routing = self.route_document(classification, content_summary)

                    results.append({
                        "path": path,
                        "type": "document",
                        "classification": classification,
                        "data_elements": data_elements,
                        "validation_requirements": validation_requirements,
                        "routing": routing
                    })
            except Exception as e:
                results.append({
                    "path": path,
                    "error": str(e),
                    "status": "failed"
                })

        return results

    def generate_triage_summary(self, batch_results):
        """Generate a summary of the document batch processing."""
        summary_prompt = PromptTemplate(
            input_variables=["batch_results"],
            template="""
            Create a summarized triage report based on the following batch processing results:

            {batch_results}

            Your triage summary should include:
            1. Total number of documents processed
            2. Breakdown by document type and classification
            3. High-priority items requiring immediate attention
            4. Documents with validation requirements or compliance concerns
            5. Recommended action plan for processing these documents
            6. Any missing information or documents that require additional review

            Format your response as a structured markdown report with clear sections and bullet points.
            """
        )

        # Create and run the summary chain
        summary_chain = LLMChain(llm=self.llm, prompt=summary_prompt)
        summary_result = summary_chain.run(batch_results=str(batch_results))

        return summary_result

    def extract_consolidated_validation_rules(self, batch_results):
        """Extract and consolidate validation rules from all documents in the batch."""
        # Collect all validation requirements
        all_requirements = []

        for result in batch_results:
            if result.get("validation_requirements") and not result.get("error"):
                requirements = result["validation_requirements"]
                if isinstance(requirements, dict) and "raw_validation" in requirements:
                    # Handle raw text case
                    continue

                # Add document source to each requirement
                for req in requirements:
                    if isinstance(req, dict):
                        req["source_document"] = result.get("path", "unknown")
                        all_requirements.append(req)

        if not all_requirements:
            return []

        # Use LLM to consolidate and remove duplicates
        consolidation_prompt = PromptTemplate(
            input_variables=["requirements"],
            template="""
            Below are validation requirements extracted from multiple documents.
            Please analyze them and:
            1. Identify duplicate or highly similar requirements
            2. Consolidate related requirements
            3. Resolve any conflicts between requirements
            4. Standardize the format and language
            5. Assign unique identifiers to each consolidated requirement

            Requirements:
            {requirements}

            Return the consolidated validation requirements in JSON format, with each requirement containing:
            - A unique identifier
            - The field or data element it applies to
            - The consolidated validation rule in clear language
            - The source documents (maintain all sources when consolidating)
            - The severity of non-compliance (using the highest severity from source requirements)
            """
        )

        # Create and run the consolidation chain
        consolidation_chain = LLMChain(llm=self.llm, prompt=consolidation_prompt)
        consolidation_result = consolidation_chain.run(requirements=str(all_requirements))

        # Try to parse as JSON, but fallback to raw text if that fails
        try:
            import json
            # Handle case where LLM might wrap JSON in markdown code blocks
            if "```json" in consolidation_result:
                json_str = consolidation_result.split("```json")[1].split("```")[0].strip()
                consolidated_json = json.loads(json_str)
            else:
                consolidated_json = json.loads(consolidation_result)
            return consolidated_json
        except:
            return {"raw_consolidation": consolidation_result}

)

# Process attachments if any
attachment_results = []
for attachment_path in email_data["attachments"]:
    att_ext = os.path.splitext(attachment_path)[1].lower()
att_content = ""

if att_ext == ".pdf":
    att_loader = PyPDFLoader(attachment_path)
att_documents = att_loader.load()
att_content = "\n".join([doc.page_content for doc in att_documents])
elif att_ext in [".txt", ".md", ".csv"]:
att_loader = TextLoader(attachment_path)
att_documents = att_loader.load()
att_content = att_documents[0].page_content if att_documents else ""

if att_content:
    att_classification = self.classify_document(att_content, attachment_path)
att_data_elements = self.extract_data_elements(att_content)

attachment_results.append({
    "path": attachment_path,
    "classification": att_classification,
    "data_elements": att_data_elements
})

# Include email metadata and attachment results
results.append({
    "path": path,
    "type": "email",
    "metadata": email_data["metadata"],
    "classification": classification,
    "data_elements": data_elements,
    "attachments": attachment_results
})

continue  # Skip the rest of the loop for emails

# For non-email documents
if content:
    classification = self.classify_document(content, path)
    data_elements = self.extract_data_elements(content)