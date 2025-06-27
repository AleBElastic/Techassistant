# app.py
from flask import Flask, request, jsonify, send_from_directory
import os
from dotenv import load_dotenv
import time
import threading
import PyPDF2
from PyPDF2 import PdfReader, PdfWriter
import logging
import requests


# Import your pdf_indexer script
# Make sure pdf_indexer.py is in the same directory as app.py
import pdf_indexer

load_dotenv() 

# Configure logging for the Flask app
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Load configuration from environment variables
ELASTICSEARCH_URL = os.getenv('ELASTICSEARCH_URL')
INDEX_NAME = os.getenv('INDEX_NAME')
API_KEY = os.getenv('API_KEY')
MODEL_ID = os.getenv('MODEL_ID', 'openai_chat_completions') # Default
UPLOAD_FOLDER = 'uploads'
SPLIT_PDF_OUTPUT_FOLDER = 'created_output'


# Directory where uploaded PDFs will be saved temporarily
# This folder will be created if it doesn't exist.

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
logging.info(f"Ensured UPLOAD_FOLDER exists: {UPLOAD_FOLDER}")

# Directory where split PDFs will be saved
os.makedirs(SPLIT_PDF_OUTPUT_FOLDER, exist_ok=True)
logging.info(f"Ensured SPLIT_PDF_OUTPUT_FOLDER exists: {SPLIT_PDF_OUTPUT_FOLDER}")

@app.route('/search_and_rag', methods=['POST'])
def search_and_rag():
    """
    Handles semantic search and RAG inference requests from the frontend.
    """
    # Validate that all necessary environment variables are loaded
    if not all([ELASTICSEARCH_URL, INDEX_NAME, API_KEY, MODEL_ID]):
        logging.error("Missing one or more environment variables for search/RAG.")
        return jsonify({'error': 'Server configuration error: Missing API keys or URLs.'}), 500

    try:
        data = request.json
        query_text = data.get('query')

        if not query_text:
            return jsonify({'error': 'Query text is required.'}), 400

        HEADERS = { # Define HEADERS inside the function or globally, but ensure API_KEY is loaded
            'Content-Type': 'application/json',
            'Authorization': f'ApiKey {API_KEY}'
        }

        # Step 1: Perform Semantic Search
        search_query = {
            "retriever": {
                "standard": {
                    "query": {
                        "semantic": {
                            "field": "body",
                            "query": query_text
                        }
                    }
                }
            },
            "highlight": {
                "fields": {
                    "body": {
                        "type": "semantic",
                        "number_of_fragments": 2,
                        "order": "score"
                    }
                }
            },
            "size": 10
        }

        logging.info(f"Performing Elasticsearch search for query: {query_text}")
        search_response = requests.post(
            f"{ELASTICSEARCH_URL}/{INDEX_NAME}/_search",
            headers=HEADERS,
            json=search_query
        )
        search_response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        search_data = search_response.json()
        search_hits = search_data.get('hits', {}).get('hits', [])
        logging.info(f"Found {len(search_hits)} search hits.")

        context_docs = [hit.get('_source', {}).get('body') for hit in search_hits if hit.get('_source', {}).get('body')]

        # Step 2: Craft the prompt for the LLM using the retrieved context
        prompt = f"""You are a specialized technician that has access to the documentation and manuals for home appliances as provided in the context. Based on the possible reasons identified for the issue, write some possible solutions organized in different bullet points and sections. Use markdown for formatting, including headings, lists, bold, and italic text. If you have no documents find in the context or the response seems incomplete, say that you do not have the answer as you do not have enough information regarding the request. Here are the found available documents that provide context:
{'\n\n'.join(context_docs)}

Question: {query_text}"""

        rag_query = {
          "input": prompt
        }

        # Step 3: Perform RAG inference using the LLM
        logging.info(f"Performing RAG inference with model: {MODEL_ID}")
        inference_response = requests.post(
            f"{ELASTICSEARCH_URL}/_inference/completion/{MODEL_ID}",
            headers=HEADERS,
            json=rag_query
        )
        inference_response.raise_for_status()
        inference_data = inference_response.json()

        generated_text = 'Could not parse the generated text from the model response.'
        if inference_data.get('completion') and len(inference_data['completion']) > 0 and inference_data['completion'][0].get('result'):
            generated_text = inference_data['completion'][0]['result']
        elif inference_data.get('choices') and len(inference_data['choices']) > 0 and inference_data['choices'][0].get('text'):
            generated_text = inference_data['choices'][0]['text']
        else:
            logging.warning(f"Unexpected inference response structure: {inference_data}")
            generated_text = "Unexpected response structure from the model. See server logs for details."


        return jsonify({'response': generated_text})

    except requests.exceptions.RequestException as e:
        logging.error(f"Error communicating with Elasticsearch or LLM: {e}")
        return jsonify({'error': f'Failed to connect to Elasticsearch/LLM: {e}'}), 500
    except Exception as e:
        logging.error(f"An unexpected error occurred during search_and_rag: {e}", exc_info=True)
        return jsonify({'error': f'An internal server error occurred: {e}'}), 500

# --- Your PDF Splitting Function (provided by you) ---
def split_pdf(input_pdf_path, output_folder, filename_prefix=''):
    """
    Splits a PDF file into individual pages and saves them to an output folder.

    Args:
        input_pdf_path (str): The full path to the input PDF file.
        output_folder (str): The directory where split pages will be saved.
        filename_prefix (str): A prefix to use for the output filenames (e.g., "manual_").
    """
    logging.info(f"[{time.strftime('%H:%M:%S')}] Splitting PDF: {input_pdf_path}")

    try:
        # Open the PDF file
        with open(input_pdf_path, 'rb') as file:
            pdf_reader = PdfReader(file)

            # Iterate through each page
            for page_num in range(len(pdf_reader.pages)):
                pdf_writer = PdfWriter()
                pdf_writer.add_page(pdf_reader.pages[page_num])

                # Generate the output file name
                # Uses the original filename (without extension) as part of the prefix
                original_filename_base = os.path.splitext(os.path.basename(input_pdf_path))[0]
                output_filename = f'{filename_prefix}{original_filename_base}_pg_{page_num + 1}.pdf'
                output_path = os.path.join(output_folder, output_filename)

                # Save the page as a new PDF
                with open(output_path, 'wb') as output_file:
                    pdf_writer.write(output_file)

                logging.info(f'[{time.strftime("%H:%M:%S")}] Saved split page: {output_filename}')
        logging.info(f"[{time.strftime('%H:%M:%S')}] Finished splitting PDF: {input_pdf_path}")
    except Exception as e:
        logging.error(f"[{time.strftime('%H:%M:%S')}] Error during PDF splitting for {input_pdf_path}: {e}")


# --- Your Background PDF Processing Function ---
def process_pdf_file(filepath):
    """
    This function handles the background processing of the uploaded PDF.
    It now calls the split_pdf function and then the pdf_indexer's main function.

    Args:
        filepath (str): The full path to the uploaded PDF file.
    """
    logging.info(f"[{time.strftime('%H:%M:%S')}] Background task: Starting to process PDF: {filepath}")

    try:
        # 1. Call the PDF splitting function here
        # You can customize the filename_prefix if needed
        logging.info(f"[{time.strftime('%H:%M:%S')}] Calling split_pdf for {filepath}...")
        split_pdf(filepath, SPLIT_PDF_OUTPUT_FOLDER, filename_prefix="uploaded_")
        logging.info(f"[{time.strftime('%H:%M:%S')}] split_pdf completed for {filepath}.")

        # 2. After splitting, call the PDF indexer to ingest the split PDFs
        # The pdf_indexer.py script is configured to look for PDFs in 'created_output/'
        logging.info(f"[{time.strftime('%H:%M:%S')}] Calling pdf_indexer.main() to index documents...")
        pdf_indexer.main() # This will process all PDFs in SPLIT_PDF_OUTPUT_FOLDER
        logging.info(f"[{time.strftime('%H:%M:%S')}] pdf_indexer.main() completed.")

        logging.info(f"[{time.strftime('%H:%M:%S')}] Background task: Finished processing and indexing {filepath}")

    except Exception as e:
        logging.error(f"[{time.strftime('%H:%M:%S')}] Background task: Error processing {filepath}: {e}")
    finally:
        # Clean up the original uploaded file after it has been processed (e.g., split and indexed)
        if os.path.exists(filepath):
            os.remove(filepath)
            logging.info(f"[{time.strftime('%H:%M:%S')}] Background task: Removed temporary uploaded file: {filepath}")

# --- Flask Routes ---

@app.route('/')
def index():
    """
    Serves the main HTML page.
    """
    return send_from_directory('.', 'rag_with_pdf.html')

@app.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    """
    Handles PDF file uploads from the frontend.
    """
    # Check if 'pdf_file' is present in the request (this name must match formData.append('pdf_file', file) in JS)
    if 'pdf_file' not in request.files:
        logging.error("[ERROR] No 'pdf_file' part in the request")
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['pdf_file']

    # Check if a file was actually selected
    if file.filename == '':
        logging.error("[ERROR] No selected file")
        return jsonify({'error': 'No selected file'}), 400

    # Validate file type (ensure it's a PDF)
    if file and file.filename.lower().endswith('.pdf'):
        # Securely generate a filename to prevent directory traversal attacks
        filename = os.path.basename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        try:
            # Save the file to the temporary upload folder
            file.save(filepath)
            logging.info(f"[{time.strftime('%H:%M:%S')}] File saved temporarily: {filepath}")

            # Start the PDF processing function in a new thread.
            # This makes the API call non-blocking for the frontend.
            # For production, consider robust task queues like Celery or RQ.
            thread = threading.Thread(target=process_pdf_file, args=(filepath,))
            thread.start()
            logging.info(f"[{time.strftime('%H:%M:%S')}] Background processing initiated for {filename}")

            return jsonify({
                'message': 'PDF uploaded successfully and background processing initiated!',
                'filename': filename,
                'status': 'processing'
            }), 200

        except Exception as e:
            # If an error occurs during saving or thread creation, clean up
            logging.error(f"[ERROR] Error during PDF upload or processing initiation: {e}")
            if os.path.exists(filepath):
                os.remove(filepath) # Remove partially saved file if something went wrong
            return jsonify({'error': f'Server error during upload: {str(e)}'}), 500
    else:
        logging.error(f"[ERROR] Invalid file type received: {file.filename}")
        return jsonify({'error': 'Invalid file type. Only PDF files are allowed.'}), 400

if __name__ == '__main__':
    # Run the Flask development server.
    # In a production environment, you would use a WSGI server like Gunicorn or uWSGI.
    logging.info(f"[{time.strftime('%H:%M:%S')}] Starting Flask server...")
    app.run(debug=True) # debug=True enables auto-reloading and better error messages
