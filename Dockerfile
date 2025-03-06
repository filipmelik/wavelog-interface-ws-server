FROM python:3.12-slim-bullseye

WORKDIR /wl-server

RUN apt-get update \
    && apt-get install -y python3-pip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt

# Copy application code
RUN mkdir -p qrg_to_mode_tables
COPY qrg_to_mode_tables qrg_to_mode_tables
COPY server.py ./
COPY run.py ./
COPY mode_from_qrg_resolver.py ./

# Command to run your application (if applicable)
CMD ["python", "run.py"]