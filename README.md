Elasticsearch Text Embedding Prework Setup
This repository contains a prework setup for integrating Elasticsearch with a text embedding model, specifically sentence-transformers__all-minilm-l6-v2. This setup demonstrates how to prepare your Elasticsearch instance to perform text embedding tasks, which can then be leveraged for semantic search and other AI-powered functionalities.
Table of Contents
Introduction
Prerequisites
Setup
1. Install the Text Embedding Model
2. Create an Inference Endpoint
3. Create an Index Mapping
Model Information
Usage
Contributing
License
Introduction
This project aims to provide a quick and easy way to get started with text embeddings in Elasticsearch. By following the steps outlined, you'll be able to:
Upload a text embedding model to your Elasticsearch instance.
Configure an inference endpoint for generating embeddings.
Create an Elasticsearch index with a semantic_text field, automatically creating embeddings for your content.
This prework is essential for any application that requires understanding the semantic meaning of text stored in Elasticsearch, such as building a PDF documentation reader, a semantic search engine, or a recommendation system.
Prerequisites
Before you begin, ensure you have the following installed and configured:
Elasticsearch Instance: A running Elasticsearch instance (version 8.x or later is recommended, as semantic_text field type and inference endpoints are modern features).
Permissions: Sufficient permissions on your Elasticsearch instance to install models and create indices/inference endpoints.
curl or a similar HTTP client: For interacting with the Elasticsearch API.
Setup
Follow these steps to set up the text embedding model and index mapping in your Elasticsearch instance.
1. Install the Text Embedding Model
The sentence-transformers__all-minilm-l6-v2 model needs to be installed in your Elasticsearch instance. A convenience script, upload_model.sh, is provided for this purpose.
Execute the script from your terminal:
./upload_model.sh


Note: Ensure the upload_model.sh script has executable permissions (chmod +x upload_model.sh) and is correctly configured to connect to your Elasticsearch instance (e.g., specifying host, port, and authentication details if required).
2. Create an Inference Endpoint
After the model is installed, you need to create an inference endpoint. This endpoint will be responsible for generating text embeddings using the installed model.
Execute the following PUT request against your Elasticsearch instance:
PUT _inference/text_embedding/minilm-l6
{
  "service": "elasticsearch",
  "service_settings": {
    "num_allocations": 1,
    "num_threads": 1,
    "model_id": "sentence-transformers__all-minilm-l6-v2"
  }
}


_inference/text_embedding/minilm-l6: Defines the endpoint named minilm-l6 under the text_embedding inference type.
service: Specifies that Elasticsearch itself will handle the inference.
service_settings: Configures the resources for the inference endpoint.
num_allocations: Number of model allocations.
num_threads: Number of threads per allocation.
model_id: The ID of the model to use for this endpoint, which corresponds to the model you installed in the previous step.
3. Create an Index Mapping
Finally, create an Elasticsearch index with a semantic_text field that leverages your newly created inference endpoint. This field type automatically generates and stores text embeddings for the content written to it.
Execute the following PUT request:
PUT pdf-documentation-reader
{
  "mappings": {
    "properties": {
      "body": {
        "type": "semantic_text",
        "inference_id": "minilm-l6"
      }
    }
  }
}


pdf-documentation-reader: The name of the new index.
mappings.properties.body: Defines a field named body within the index.
type: "semantic_text": Specifies that this field is a semantic text field, designed to store and automatically embed text.
inference_id: "minilm-l6": Links this semantic_text field to the minilm-l6 inference endpoint created earlier. Any text indexed into the body field will now automatically be processed by the sentence-transformers__all-minilm-l6-v2 model to generate its embedding.
Model Information
This example relies on the sentence-transformers__all-minilm-l6-v2 model, which is a popular and efficient choice for text embedding tasks.
Model Name: sentence-transformers/all-MiniLM-L6-v2
Source: Hugging Face Hub
Description: A sentence transformer model that maps sentences & paragraphs to a 384-dimensional dense vector space and can be used for tasks like semantic search, clustering, and paraphrase identification.
You can find more information about this model on the Hugging Face Hub.
Usage
Once the setup is complete, you can start indexing your PDF content (or any text content) into the pdf-documentation-reader index. For example:
POST pdf-documentation-reader/_doc
{
  "body": "This is a document about setting up Elasticsearch for text embedding. It covers model installation and index mapping."
}


Elasticsearch will automatically create an embedding for the body field. You can then perform semantic search queries using the text_embedding query type or similar semantic search functionalities provided by Elasticsearch.
Contributing
Feel free to contribute to this project by opening issues or submitting pull requests.
