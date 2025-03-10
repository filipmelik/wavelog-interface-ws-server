# stage 1: build
FROM python:3.12-slim-bullseye AS builder

WORKDIR /wl-server

RUN apt-get update \
    && apt-get install -y python3-pip \
    && rm -rf /var/cache/apt/archives /var/lib/apt/lists/*

COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt

COPY server.py ./
COPY run.py ./
COPY mode_from_qrg_resolver.py ./

# stage 2: actual image
FROM python:3.12-slim-bullseye AS runner

WORKDIR /wl-server

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /wl-server /wl-server

# Command to run your application (if applicable)
CMD ["python", "run.py"]