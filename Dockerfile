FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

#ENV UV_INDEX_URL=

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    procps \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && NODE_MAJOR=22 \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update && apt-get install -y nodejs --no-install-recommends \
    && npm install -g pnpm \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g @marp-team/marp-cli

RUN pip install uv

WORKDIR /app

COPY . .

RUN uv sync

RUN cd web && cp .env.example .env && pnpm install && cd ..

RUN cp .env.example .env
RUN cp conf.yaml.example conf.yaml

RUN chmod +x ./bootstrap.sh

EXPOSE 8000
EXPOSE 3000

CMD ["./bootstrap.sh", "-d"]
