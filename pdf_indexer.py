import os
from elasticsearch import Elasticsearch
from pdfminer.high_level import extract_text
import logging

ELASTIC_API_KEY="OFdrNW1KY0JfLWplR05TSV9lTXI6YTZfcDlkZ05jRy12czc5dkpVRmpFdw"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_es_client(host='localhost', port=9200, api_key=None, cloud_id=None, user=None, password=None):

    if cloud_id and api_key:
        logging.info(f"Connecting to Elasticsearch Cloud using Cloud ID: {cloud_id}")
        return Elasticsearch(
            cloud_id=cloud_id,
            api_key=api_key,
            request_timeout=60 # Add a timeout for requests
        )
    else:
        raise ValueError("Insufficient Elasticsearch connection parameters provided.")


def extract_text_from_pdf(pdf_path):
    """
    Extracts text content from a given PDF file.
    """
    try:
        logging.info(f"Extracting text from {pdf_path}")
        text = extract_text(pdf_path)
        return text
    except Exception as e:
        logging.error(f"Error extracting text from {pdf_path}: {e}")
        return None

def index_pdf_document(es_client, index_name, doc_id, file_path, content):
    """
    Indexes a single PDF document's content into Elasticsearch.
    """
    document = {
        "file_name": os.path.basename(file_path),
        "file_path": os.path.abspath(file_path),
        "body": content
    }
    try:
        # Check if the index exists, create if not
        if not es_client.indices.exists(index=index_name):
            logging.info(f"Index '{index_name}' does not exist. Creating it.")
            es_client.indices.create(index=index_name)

        response = es_client.index(index=index_name, id=doc_id, document=document)
        logging.info(f"Successfully indexed '{os.path.basename(file_path)}' with ID: {response['_id']}")
        return response
    except Exception as e:
        logging.error(f"Error indexing document '{os.path.basename(file_path)}': {e}")
        return None

def main():
    """
    Main function to orchestrate reading PDFs and indexing them.
    """
    # --- Configuration ---
    # Set the path to your PDF folder
    PDF_FOLDER_PATH = "./created_output/" # IMPORTANT: Change this to your actual PDF folder path!

    # Elasticsearch Connection Details
    # Choose ONE of the following configurations based on your Elasticsearch setup:

    # Option 1: Local Elasticsearch (No Auth) - NOT RECOMMENDED FOR PRODUCTION
    ES_API_KEY = 'OFdrNW1KY0JfLWplR05TSV9lTXI6YTZfcDlkZ05jRy12czc5dkpVRmpFdw'
    ES_CLOUD_ID = 'playgorund-v2:c6ea14089eff4d9698f98e0c2b81dcaa'
    ES_USER = None
    ES_PASSWORD = None
    ES_HOST = None


    # Elasticsearch Index Name
    ES_INDEX_NAME = 'pdf-documentation-reader'

    # --- End Configuration ---

    if not os.path.isdir(PDF_FOLDER_PATH):
        logging.error(f"PDF folder path '{PDF_FOLDER_PATH}' does not exist or is not a directory.")
        return

    try:
        es = Elasticsearch(hosts="https://playgorund-v2.es.europe-west9.gcp.elastic-cloud.com", api_key="OFdrNW1KY0JfLWplR05TSV9lTXI6YTZfcDlkZ05jRy12czc5dkpVRmpFdw")
        # Verify connection
        if not es.ping():
            raise ValueError("Could not connect to Elasticsearch! Check your connection details.")
        logging.info("Successfully connected to Elasticsearch.")

    except Exception as e:
        logging.critical(f"Failed to establish Elasticsearch connection: {e}")
        return

    for filename in os.listdir(PDF_FOLDER_PATH):
        if filename.lower().endswith(".pdf"):
            pdf_file_path = os.path.join(PDF_FOLDER_PATH, filename)
            doc_id = os.path.splitext(filename)[0] # Use filename (without extension) as document ID

            pdf_content = extract_text_from_pdf(pdf_file_path)

            if pdf_content:
                index_pdf_document(es, ES_INDEX_NAME, doc_id, pdf_file_path, pdf_content)
            else:
                logging.warning(f"Skipping '{filename}' due to empty or unextractable content.")

if __name__ == "__main__":
    main()