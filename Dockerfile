# Sealed, reproducible runtime for the blast-radius-containment experiment.
# Build:  docker build -t blast-radius .
# Run:    docker run --rm blast-radius   (tests + experiment + provenance)
FROM python:3.13-slim

WORKDIR /app

# Dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Source
COPY . .

# Default: verify the artifact end to end.
CMD ["sh", "-c", "python -m pytest -q && python run_all.py && python make_provenance.py"]
