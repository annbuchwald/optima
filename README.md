# Function Optimization Assistant

This project is an AI assistant designed to provide expert recommendations on function optimization across multiple programming languages. It integrates Azure OpenAI (for both chat and embeddings) with Azure Cognitive Search using the LangChain framework.

## Features

- Uses Azure OpenAI for language understanding and response generation
- Retrieves contextually relevant documents from Azure Cognitive Search
- Answers include algorithmic suggestions, code examples, and performance tradeoffs
- Automatic retry and fallback mechanisms to handle API or network failures
- Built-in .env validation and logging for reliable deployment

## Requirements

- Python 3.10+
- Azure OpenAI resource (with deployed chat and embedding models)
- Azure Cognitive Search instance and populated index

## Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/function-optimization-assistant.git
   cd function-optimization-assistant

## GUI

optima_gui.py serves as a configuration frontend for initiating static complexity analysis using optima_backend.py.

## Functionalities:

Select analysis scope: file-level or directory-level traversal

Load paths via native file/directory dialogs

Configure maximum cyclomatic complexity threshold (integer input)

Define function matching criteria via regex patterns (multiline input)

Restrict analysis to specific file extensions (e.g., .py, .java)

Optional inclusion of line number ranges in output

Displays results in a read-only, scrollable log view

Implements dark-themed text UI and inline input validation

## Execution
Ensure optima_backend.py is present in the project root. Then run:

bash
python optima_gui.py
