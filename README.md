# Contract Processing Pipeline

A comprehensive Python pipeline for processing legal contracts using Firebase, Vertex AI, and modern ML techniques.

## Features

- **OCR & Text Extraction**: Tesseract OCR for scanned PDFs, pdfplumber for text-based PDFs
- **Layout & Semantic Parsing**: LayoutLMv3 integration for document understanding
- **Preprocessing & Normalization**: spaCy + LangChain for text processing and entity extraction
- **Embeddings & Vector Storage**: Hugging Face embeddings with Supabase pgvector
- **RAG & Text Generation**: Vertex AI with LangChain for summaries and analysis
- **Cloud Infrastructure**: Firebase Functions, Firestore, and Storage triggers

## Tech Stack

- **Storage**: Firebase Storage with automatic triggers
- **Functions**: Firebase Functions for serverless processing
- **Document Parsing**: Tesseract OCR, pdfplumber, LayoutLMv3
- **Preprocessing**: spaCy + LangChain
- **Embeddings**: Hugging Face sentence-transformers + Supabase vector DB
- **Text Generation**: Vertex AI (Google Cloud)
- **Database**: Firestore for metadata, Supabase for vectors
## Installation

```bash
# Clone repository and install dependencies
pip install -r requirements.txt

# Download required models
python -m spacy download en_core_web_sm

# Set up Firebase
npm install -g firebase-tools
firebase login
firebase init

# Copy environment configuration
cp .env.example .env
# Edit .env with your Firebase project ID and Google Cloud credentials
```

## API Server

The project includes a comprehensive FastAPI backend for frontend integration:

### Quick Start

```bash
# Install API dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the API server
python run_api.py
```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or run individual services
docker build -t contract-api .
docker run -p 8000:8000 contract-api
```

### API Features

- **Contract Upload & Processing**: Upload PDF contracts for automated processing
- **Real-time Updates**: WebSocket connections for processing progress
- **Contract Analysis**: Comprehensive legal analysis with risk assessment
- **Question Answering**: RAG-powered Q&A about contract content
- **Search & Discovery**: Semantic search across contracts
- **Batch Processing**: Process multiple contracts simultaneously
- **Analytics**: Processing metrics and insights
- **Export**: Download contracts and analysis in various formats

### API Endpoints

#### Contract Management
- `POST /api/contracts/upload` - Upload contract file
- `GET /api/contracts` - List user contracts
- `GET /api/contracts/{id}` - Get contract details
- `DELETE /api/contracts/{id}` - Delete contract
- `POST /api/contracts/{id}/process` - Start processing
- `GET /api/contracts/{id}/status` - Get processing status

#### Analysis & Q&A
- `GET /api/contracts/{id}/analysis` - Get contract analysis
- `POST /api/contracts/{id}/question` - Ask questions about contract
- `POST /api/contracts/search` - Search contracts
- `GET /api/contracts/{id}/similar` - Find similar contracts

#### Batch Operations
- `POST /api/contracts/batch` - Start batch processing
- `GET /api/batch/{id}/status` - Get batch status

#### File Operations
- `GET /api/contracts/{id}/download` - Download original file
- `GET /api/contracts/{id}/export` - Export analysis

#### Real-time Updates
- `WS /ws/{user_id}` - WebSocket for real-time notifications

#### Analytics
- `GET /api/analytics/overview` - Processing metrics
- `GET /api/analytics/user` - User analytics
- `GET /api/analytics/trends` - Processing trends

### Authentication

The API uses JWT tokens for authentication. For development, use the token `dev-token`.

Production deployment should integrate with Firebase Auth or another authentication provider.

### Frontend Integration

The API is designed to work with modern frontend frameworks:

```javascript
// Example: Upload and process contract
const formData = new FormData();
formData.append('file', contractFile);

const response = await fetch('/api/contracts/upload', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer your-jwt-token'
  },
  body: formData
});

const result = await response.json();
console.log('Contract uploaded:', result.contract_id);

// WebSocket for real-time updates
const ws = new WebSocket('ws://localhost:8000/ws/user-id');
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  if (update.type === 'processing_update') {
    console.log('Processing progress:', update.data.progress);
  }
};
```

## Configuration

1. Set up Firebase project with Storage and Firestore
2. Enable Vertex AI in Google Cloud Console
3. Set up Supabase with pgvector extension for vector storage
4. Configure service account credentials
3. Download required models (spaCy, sentence-transformers)

## Firebase Deployment

```bash
# Deploy Firebase Functions
cd firebase
firebase deploy --only functions

# Deploy Firestore rules
firebase deploy --only firestore:rules

# Deploy Storage rules
firebase deploy --only storage
```
## Usage

### Firebase Functions (Automatic)

Upload PDF files to Firebase Storage `/contracts/` folder - processing happens automatically via triggers.

### Command Line Interface

```bash
# Process single contract
python cli.py process contract.pdf --output-dir ./output

# Batch process multiple contracts
python cli.py batch ./contracts --output-dir ./batch_output

# Set up environment
python cli.py setup

# Analyze processed contract
python cli.py analyze processed_contract.json --question "What are the payment terms?"
```

### Python API

```python
from pipeline.orchestrator import ContractPipeline

# Initialize pipeline
pipeline = ContractPipeline()

# Process contract
result = pipeline.process_contract("contract.pdf", "./output")

# Generate summary
summary = pipeline.rag_generator.generate_summary(result['contract'])
```

### HTTP API Endpoints

```bash
# Process contract manually
curl -X POST https://your-project.cloudfunctions.net/process_contract_api \
  -H "Content-Type: application/json" \
  -d '{"file_path": "contracts/sample.pdf"}'

# Query contract using RAG
curl -X POST https://your-project.cloudfunctions.net/query_contract_api \
  -H "Content-Type: application/json" \
  -d '{"contract_id": "sample", "question": "What are the payment terms?"}'
```

## Pipeline Steps

1. **OCR/Text Extraction** → Raw text from PDF
2. **Layout Parsing (LayoutLMv3)** → Structured sections and clauses
3. **Preprocessing (spaCy + LangChain)** → Normalized text with entities
4. **Embeddings** → Vector representations of clauses
5. **Vector Storage** → Supabase pgvector database
6. **RAG Analysis (Vertex AI)** → AI-generated summaries and insights
7. **Storage** → Results stored in Firestore

## Architecture

```
├── firebase/         # Firebase Functions and configuration
│   ├── functions/
│   ├── firestore.rules
│   └── storage.rules
├── models/           # Pydantic data models
├── pipeline/         # Core processing modules
│   ├── ocr_extractor.py
│   ├── layout_parser.py
│   ├── preprocessor.py
│   ├── embedder.py
│   ├── rag_generator.py
│   ├── firestore_manager.py
│   └── orchestrator.py
├── config.py         # Configuration settings
├── cli.py           # Command-line interface
└── main.py          # Example usage
```

## Firebase Integration

The pipeline integrates with Firebase services:

- **Firebase Functions**: Serverless processing with automatic triggers
- **Firebase Storage**: File upload triggers for automatic processing
- **Firestore**: Metadata storage
- **Vertex AI**: Text generation and analysis
- **Supabase**: Vector storage for similarity search

## TODO: Implementation Details

Each module contains detailed TODO comments for implementation:

- OCR with confidence scoring and image preprocessing
- LayoutLMv3 integration for semantic understanding
- Custom legal entity patterns for spaCy
- Vector similarity search optimization
- LLM prompt engineering for legal analysis
- Batch processing with progress tracking
- Error handling and logging
- Cloud deployment automation

## License

MIT License - see LICENSE file for details