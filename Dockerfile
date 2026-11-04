# Image for Hugging Face Spaces (Docker SDK). Serves the app on port 7860.
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
# CPU-only torch first; the CUDA build from PyPI is several GB.
RUN pip install --no-cache-dir torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

# Spaces run the container as uid 1000.
RUN useradd -m -u 1000 user
COPY --chown=user . .
RUN chown user /app
USER user
ENV HOME=/home/user

# Download the model and build the vector index into the image, then stay offline at runtime.
RUN python -m src.indexer
ENV HF_HUB_OFFLINE=1

EXPOSE 7860
CMD ["streamlit", "run", "src/app.py", "--server.address=0.0.0.0", "--server.port=7860", "--server.headless=true"]
