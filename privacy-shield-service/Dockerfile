# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- CHANGE THIS LINE ---
# Copy the CONTENTS of the app directory into the working directory
COPY ./app/ .

# --- CHANGE THIS LINE ---
# Update the CMD to run main:app directly
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]