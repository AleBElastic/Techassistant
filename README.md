# Tech Assistant for home appliances

This repository provides a prework setup for integrating Elasticsearch with the `sentence-transformers__all-minilm-l6-v2` text embedding model. This guide will show you how to prepare your Elasticsearch instance for text embedding tasks, which you can then use for semantic search and other AI-powered functionalities.

---

## Introduction

This guide offers a quick and easy way to get started with text embeddings in Elasticsearch. By following these steps, you'll be able to:

- Upload a text embedding model to your Elasticsearch instance.
- Configure an inference endpoint for generating embeddings.
- Create an Elasticsearch index with a `semantic_text` field, which will automatically create embeddings for your content.

This prework is essential for any application that needs to understand the semantic meaning of text, like building a documentation reader, a semantic search engine, or a recommendation system.

---

## Prerequisites

Before you begin, make sure you have the following installed and configured:

- **Elasticsearch Instance**: A running Elasticsearch instance (version 8.x or later is recommended, as `semantic_text` field type and inference endpoints are modern features).
- **Permissions**: Sufficient permissions on your Elasticsearch instance to install models and create indices/inference endpoints.
- **curl or a similar HTTP client**: A tool like `curl` or any other HTTP client is needed to interact with the Elasticsearch API.

---

## Setup

Follow these steps to set up the text embedding model and index mapping in your Elasticsearch instance.

### 1. Install the Text Embedding Model

First, the `sentence-transformers__all-minilm-l6-v2` model must be installed in your Elasticsearch instance. You can do this using the provided `upload_model.sh` script, which automates the download and installation process.

**Execute the script from your terminal:**

```bash
./upload_model.sh
```

> **Note**: Ensure the script has executable permissions:
>
> ```bash
> chmod +x upload_model.sh
> ```

---

### 2. Create an Inference Endpoint

Next, create an inference endpoint. This endpoint makes the installed model available to Elasticsearch services, such as the `semantic_text` field type. It defines how the model should be allocated and used for generating embeddings.

**Execute the following PUT request:**

```http
PUT _inference/text_embedding/minilm-l6
{
  "service": "elasticsearch",
  "service_settings": {
    "num_allocations": 1,
    "num_threads": 1,
    "model_id": "sentence-transformers__all-minilm-l6-v2"
  }
}
```

- `_inference/text_embedding/minilm-l6`: Defines the endpoint named `minilm-l6` under the `text_embedding` inference type.
- `service`: Specifies that Elasticsearch itself will handle the inference.
- `service_settings`: Configures the resources for the inference endpoint.
  - `num_allocations`: Number of model allocations.
  - `num_threads`: Number of threads per allocation.
  - `model_id`: The ID of the model to use for this endpoint, which corresponds to the model you installed in the previous step.

---

### 3. Create an Index Mapping

Create an Elasticsearch index with a `semantic_text` field. This special field type is linked to your inference endpoint and will automatically generate and store embeddings for any text you index into it.

**Execute the following PUT request:**

```http
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
```

- `pdf-documentation-reader`: The name of the new index.
- `mappings.properties.body`: Defines a field named `body` within the index.
  - `type: "semantic_text"`: Specifies that this field is a semantic text field, designed to store and automatically embed text.
  - `inference_id: "minilm-l6"`: Links this `semantic_text` field to the `minilm-l6` inference endpoint created earlier.

---

## Ready for Use

With the setup complete, your index is ready. You can now start indexing documents. Elasticsearch will automatically handle the creation of embeddings for the `body` field, enabling you to perform powerful semantic searches.

**Example document indexing:**

```http
POST pdf-documentation-reader/_doc
{
  "body": "This is a document about setting up Elasticsearch for text embedding. It covers model installation and index mapping."
}
```

---

## Contributing

Feel free to contribute to this project by opening issues or submitting pull requests.

