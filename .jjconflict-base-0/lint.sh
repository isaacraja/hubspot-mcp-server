#!/bin/bash

# Run Ruff formatters and linters
echo "Running Ruff format..."
ruff format .

echo "Running Ruff check..."
ruff check .

echo "Done!" 