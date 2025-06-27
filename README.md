# Elasticsearch Text Embedding Prework Setup

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

