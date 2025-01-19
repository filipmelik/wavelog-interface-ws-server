FROM python:3.12-slim-bullseye

WORKDIR /wl-server

RUN apt-get update \
    && apt-get install -y python3-pip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server.py ./
COPY run.py ./

# Command to run your application (if applicable)
CMD ["python", "run.py"]