# --- Builder Stage ---
FROM python:3.11-slim as builder

ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# --- Final Stage ---
FROM python:3.11-slim as final

ENV DEBIAN_FRONTEND=noninteractive

# Install runtime dependencies - using more compatible packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# The problematic packages (libgl1-mesa-glx, libsm6, libxext6, libxrender-dev) 
# are often not needed for headless operation. If you need them, install separately:
# RUN apt-get update && apt-get install -y libgl1-mesa-glx libsm6 libxext6 libxrender1 && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --system app && useradd --system --gid app app
USER app
WORKDIR /home/app

# Copy virtual environment and application code
COPY --from=builder /opt/venv /opt/venv
COPY . .

# Create necessary directories
RUN mkdir -p uploads outputs exports logs

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/home/app
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata

# Run the application
CMD ["python", "run_api.py"]