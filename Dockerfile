# --- Builder Stage ---
# This stage prepares the Python environment and handles build-time dependencies.
FROM python:3.11-slim as builder

ENV DEBIAN_FRONTEND=noninteractive

# Install build-essential for any Python packages that need compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy requirements and install Python dependencies into the virtual environment
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Download the spaCy model into the virtual environment's site-packages
RUN python -m spacy download en_core_web_sm


# --- Final Stage ---
# This stage creates the final, lean image for running the application.
FROM python:3.11-slim as final

ENV DEBIAN_FRONTEND=noninteractive

# Install only the necessary RUNTIME system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        poppler-utils \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender-dev \
        libgomp1 \
        curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user and group for security
RUN groupadd --system app && useradd --system --gid app app
USER app
WORKDIR /home/app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy the application code
COPY . .

# Create necessary directories (Render will mount over 'uploads')
RUN mkdir -p uploads outputs exports logs

# Set environment variables for the runtime
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/home/app
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata
# Let Render set the PORT dynamically
# EXPOSE 8000 # Good for documentation, but Render uses its own PORT variable

# Health check
# Note: Render uses its own health check system defined in render.yaml,
# but this is good for local testing.
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Run the application using the startCommand from your render.yaml
# This CMD is a fallback for local testing. Render will override it.
CMD ["python", "run_api.py"]

