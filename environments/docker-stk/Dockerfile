FROM python:3.12-slim-bookworm@sha256:54c85f3c47607a77f32adec749d3c81d1348bf25833671f512b26a9b6d778cb3
ARG BUILD_JOBS=2
ENV DEBIAN_FRONTEND=noninteractive PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ make cmake pkg-config libbluetooth-dev libcurl4-gnutls-dev \
    libfreetype6-dev libharfbuzz-dev libjpeg-dev libogg-dev libopenal-dev \
    libpng-dev libsdl2-dev libvorbis-dev zlib1g-dev libgl1-mesa-dev \
    libegl1-mesa-dev libgl1-mesa-dri libssl-dev ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY . /source
WORKDIR /source
ENV CMAKE_BUILD_PARALLEL_LEVEL=${BUILD_JOBS} SETUPTOOLS_SCM_PRETEND_VERSION=0.7.4+ggbrender1
ENV CMAKE_ARGS="-DNO_SHADERC=ON -DUSE_GLES2=OFF"
RUN python -m pip install . 'numpy==1.26.4' 'pillow==11.3.0' \
    'platformdirs==4.12.3' 'requests==2.34.2' 'certifi==2026.7.22' \
    'charset-normalizer==3.5.2' 'idna==3.20' 'urllib3==2.8.0'
LABEL org.generalgamebench.engine-revision="dd70f6823f248ae1df2ce513839a9b2c8c940c39"
LABEL org.generalgamebench.variant="deterministic-render-v1"
WORKDIR /tmp
ENV SDL_VIDEODRIVER=offscreen SDL_AUDIODRIVER=dummy LIBGL_ALWAYS_SOFTWARE=1
ENV SUPERTUXKART_DATADIR=/assets LP_NUM_THREADS=1
ENTRYPOINT ["python", "-u"]
