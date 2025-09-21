# --- Builder Stage ---
FROM python:3.11-slim-bookworm as builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Skip spaCy model download in Docker build - will be handled at runtime

# --- Final Stage ---
FROM python:3.11-slim-bookworm as final

ENV DEBIAN_FRONTEND=noninteractive

# Install ONLY the packages your backend actually needs
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libglib2.0-0 \
    libgomp1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system app && useradd --system --gid app app
USER app
WORKDIR /home/app

COPY --from=builder /opt/venv /opt/venv
COPY . .

RUN mkdir -p uploads outputs exports logs

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/home/app
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata

CMD ["python", "startup.py"]