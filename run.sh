#!/bin/bash

# Load environment variables from .env.local
export $(cat .env.local | xargs)

# Set the vault path (modify this to your actual vault path)
export VAULT_PATH="./notes"

# Create the notes directory if it doesn't exist
mkdir -p ./notes
mkdir -p ./uploads

# Install the package in development mode
pip install -e .

# Run the application
python app.py 