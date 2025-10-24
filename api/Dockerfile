FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    tesseract-ocr \
    libtesseract-dev \
    libheif1 \
    libheif-dev \
    libexiv2-dev \
    libboost-python-dev \
    libboost-all-dev \
    build-essential \
    pkg-config \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Ensure Boost Python linker aliases exist (needed by py3exiv2 build)
RUN ldconfig && \
    so_target="$(find /usr/lib /usr/lib/aarch64-linux-gnu -name 'libboost_python*so*' -print 2>/dev/null | head -n1)" && \
    if [ -n "$so_target" ]; then \
        so_dir="$(dirname "$so_target")"; \
        so_file="$(basename "$so_target")"; \
        if [ ! -f "${so_dir}/libboost_python311.so" ]; then \
            ln -s "$so_file" "${so_dir}/libboost_python311.so"; \
        fi; \
    fi && \
    a_target="$(find /usr/lib /usr/lib/aarch64-linux-gnu -name 'libboost_python*.a*' -print 2>/dev/null | head -n1)" && \
    if [ -n "$a_target" ]; then \
        a_dir="$(dirname "$a_target")"; \
        a_file="$(basename "$a_target")"; \
        if [ ! -f "${a_dir}/libboost_python311.a" ]; then \
            ln -s "$a_file" "${a_dir}/libboost_python311.a"; \
        fi; \
    fi

# Upgrade pip, setuptools, and wheel
RUN pip install --upgrade pip setuptools wheel

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/healthz || exit 1

# Run the application with full verification API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
