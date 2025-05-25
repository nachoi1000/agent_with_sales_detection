# QuantumChain Chatbot Agent
This project involves the development of an intelligent chatbot agent designed to answer questions about QuantumChain Technologies, a fictional company created for the purposes of this project.

In addition to providing informative responses about QuantumChain's products, services, and general operations, the agent is equipped with advanced capabilities to detect potential user interest in the company's offerings. If such interest is identified, and explicit user consent is obtained, the agent transitions into a more proactive role, requesting personal contact information from the user for potential follow-up by the (simulated) company.

The agent architecture is modular and includes several assistant components responsible for sales intention detection, consent detection, security filtering, and conversation memory management, enabling smooth orchestration between informative interaction and sales-oriented engagement.

---

## 🧪 Project Overview

This project was designed to apply and integrate knowledge from both **Artificial Intelligence** and **Software Engineering**.

The development was carried out entirely **from scratch**. It includes:

- Generating synthetic company data using **LLMs**.
- Preprocessing and chunking that data.
- Storing the processed data in a **ChromaDB** vector database.
- Retrieving relevant information to use as **context in prompts**.

The formats of the data that can be processed and ingested into Vectordatabase are: **.pdf** (Native (digitally created) or Scanned with OCR, not Scanned without OCR), **.txt**, **.md**, **.doc** and **.docx**.

To enhance retrieval quality, **four different strategies** were implemented and can be configured dynamically.


### 🧠 Prompt Engineering

All prompts are stored in `.md` format for clarity and maintainability.

- The **sales detector** and **consent detector** prompts follow a **Few-Shot Learning** approach, providing example inputs and classifications to guide the LLM toward more accurate classifications.

- The **RAG prompt** combines:
  - A **static context** that introduces the company and general instructions.
  - A **dynamic context** built from the relevant documents retrieved via the vector store.

This combination allows the LLM to generate highly contextualized and grounded responses.

---

## 🔧 Technologies Used

- Python 3.10+
- [Quart](https://pgjones.gitlab.io/quart/)
- [OpenAI API](https://platform.openai.com/)
- [MongoDB](https://www.mongodb.com/)
- [ChromaDB](https://www.trychroma.com/)
- Docker

---

## 🚀 Running the project
At the root, create a .env file using env.Sample as a template.

On **Linux**, run: `./start.sh`  
On **Windows**, run: `./start.ps1`

App runs on: `http://localhost:5000` 
MongoDB container exposed on: `localhost:27017`

> **Note**: Stopping the app does **not** stop the MongoDB container. You must stop/remove it manually if needed.

---

# Agent flow
[![Agent main flow](docs/main_flow.svg)](docs/main_flow.svg)

1. **Input received** from user.  
2. **Safety filtering** is applied to ensure the message is appropriate.  
3. **Conversation history** is retrieved to maintain context.  
4. **Sales interest** is detected.  
5. **Consent** is checked.  
6. Based on context, an appropriate **response** is generated.

Let’s explore the main assistants in more detail:

**Assistant RAG**

[![Assistant RAG](docs/RAG.svg)](docs/RAG.svg)

Handles the main Q&A using vector search and context retrieval.

**Assistant Sales Detector**

[![Assistant Sales Detector](docs/assistant_sales_detector.svg)](docs/assistant_sales_detector.svg)

Detects sales intent in user input.

**Assistant Consent Detector**

[![Assistant Consentiment Detector](docs/assistant_consent_detector.svg)](docs/assistant_consent_detector.svg)

Detects whether the user has given consent to share personal information.

**Assistant Memory**

[![Assistant Memory](docs/assistant_memory.svg)](docs/assistant_memory.svg)

Reconstructs the conversation history from stored messages.

**Assistant Request Data**

[![Assistant Request Data](docs/assistant_request_data.svg)](docs/request_data.svg)

Scrap user conversation to obtain *name* and *email* if one is missing it will request it on the generated answer. 

---

## Important classes

**LLM Classes**

There is a class to manage the basic OpenAI ChatCompletion requests.
And there is a class to intanciate the Assistants and other for RAG.

**Chromadb vectordatabase and retriever**

ChromaVectorStore is the class that manages ChromaDB Vectorstore.
 It has 2 main responsibilities:
- **Data ingestion**: Manages document storage in the collection (chunking, IDs, metadata, and embeddings).
- **Retrieval**: The `RetrievalStrategies` class (inside `ChromaVectorStore`) retrieves relevant context (Retrieval-Augmented Generation) to be used as grounding for the RAG. Four configurable strategies are available.


**MongoDBManager**

MongoDBManager is the class that manages MongoDB Database.
This project use 1 database with 2 collections.
One collection stores all conversation messages between the user and the agent.
The other collection is used to store the user personal data that will be used for future contact.

This class has 2 main useful methods: 
- buscar_conversaciones_por_id: *Searches conversations by their ID.*
- add_item: *Adds a document to the selected collection.*

---

## Project Structure
<pre><code>
.
├── storage/                         # Modules for persistent data management
│   ├── db/                          # MongoDB interface and database logic
│   │   ├── __init__.py
│   │   └── db_manager.py
│   └── vector_db/                   # Vector database interaction layer
│       ├── __init__.py
│       └── vectorstore.py
│
├── prompts/                         # Prompt templates for different assistant tasks
│   ├── __init__.py
│   ├── consentiment.md              # Prompt for detecting user consent
│   ├── content_filter.md            # Prompt for filtering inappropriate or insecure content
│   ├── conversation_memory.md       # Prompt for reconstructing conversation context
│   ├── quantum_rag.md               # RAG prompt for answering questions about QuantumChain
│   ├── request_user_data.md         # Prompt for collecting user data (with previous consent)
│   └── sales_detector.md            # Prompt for identifying sales interest
│
├── utils/                           # Core utilities and helper classes
│   ├── __init__.py
│   ├── conversation.py              # Conversation data models
│   ├── file_manager.py              # Utilities for handling files
│   ├── llm_manager.py               # LLM interaction and API handling
│   ├── logger.py                    # Logging setup
│   └── user_data.py                 # Extraction and validation of user information
│
├── frontend/                        # HTML frontend for the chatbot
│   └── index.html
│
├── data_ingestion/                 # Ingests and processes source documents for retrieval
│   ├── data/                        # Contains raw PDF files about QuantumChain
│   └── indexing/
│       ├── __init__.py
│       ├── chunker.py               # Splits documents into chunks
│       ├── document_handler.py      # Loads and processes documents
│       ├── documents.py             # Document representation
│       ├── loader.py                # Data loading utilities
│       └── vectorizer.py            # Embedding and vector storage
│
├── docs/                            # Static files used in documentation (e.g., images)
│
├── logs/                            # Stores runtime logs
│
├── vectorstore/                     # Local vector store (e.g., Chroma DB files)
│
├── mongo_database/                  # Docker volume to persist MongoDB data locally
│
├── app.py                           # Main application entrypoint
├── main.py                          # Bootstraps and runs the chatbot system
├── config.py                        # Configuration and environment variable management
├── provision.py                     # Initializes the vector store and loads documents
│
├── .env                             # Environment variables (used in production)
├── env.Sample                       # Sample environment config
</code></pre>
---

## ✅ Requirements
Make sure you have the following installed:

- Python 3.10 or higher
- `pip` or `poetry`
- Docker & Docker Compose
- OpenAI API Key

## 📩 Contact

For any questions or feedback related to this project, feel free to open an issue or contact the developer.



