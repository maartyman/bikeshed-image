FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        default-jre-headless \
        git \
        graphviz \
        inotify-tools \
    && rm -rf /var/lib/apt/lists/*

# Install a recent PlantUML jar to support themes.
RUN curl -fsSL -o /usr/local/lib/plantuml.jar \
        "https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar" \
    && printf '%s\n' \
        '#!/usr/bin/env bash' \
        'exec java -jar /usr/local/lib/plantuml.jar "$@"' \
        > /usr/local/bin/plantuml \
    && chmod +x /usr/local/bin/plantuml

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir bikeshed livereload \
    && bikeshed update

COPY plantuml.py /usr/local/bin/plantuml.py
COPY docker-entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

WORKDIR /work
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
EXPOSE 59754
