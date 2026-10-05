FROM python:3.12-slim-trixie@sha256:02108f5d322dd89f1c9e552442c25acb0543dfdbc455693a5599624f20d9155d
ARG REVISION=development
LABEL org.opencontainers.image.source="https://github.com/DanielTea/generalgamebench" \
      org.opencontainers.image.title="GeneralGameBench portable runner" \
      org.opencontainers.image.revision="$REVISION"
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libsdl2-2.0-0 libsndfile1 libopenal1 libgomp1 \
    && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --no-cache-dir uv==0.9.26
WORKDIR /opt/ggbench
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
COPY docs/THIRD_PARTY_NOTICES.md ./docs/THIRD_PARTY_NOTICES.md
RUN uv sync --frozen --extra doom --no-dev --no-editable
ENV PATH="/opt/ggbench/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 HOME=/tmp \
    SDL_AUDIODRIVER=dummy SDL_VIDEODRIVER=dummy \
    GGBENCH_IMAGE_REVISION="$REVISION"
WORKDIR /tmp
USER 1000:1000
ENTRYPOINT ["generalgamebench"]
CMD ["benchmark", "--output", "/results/submission"]
