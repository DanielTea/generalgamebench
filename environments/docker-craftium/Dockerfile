FROM python:3.12-slim-bookworm@sha256:54c85f3c47607a77f32adec749d3c81d1348bf25833671f512b26a9b6d778cb3
ARG BUILD_JOBS=2
ENV DEBIAN_FRONTEND=noninteractive PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ make cmake libpng-dev libjpeg-dev libgl1-mesa-dev libegl1-mesa-dev \
    libsqlite3-dev libogg-dev libvorbis-dev libopenal-dev libcurl4-gnutls-dev \
    libfreetype6-dev zlib1g-dev libgmp-dev libjsoncpp-dev libzstd-dev \
    libluajit-5.1-dev gettext libsdl2-dev libspatialindex-dev \
    libgl1-mesa-dri ca-certificates && rm -rf /var/lib/apt/lists/*
COPY . /source
WORKDIR /source
RUN cmake -B build -DRUN_IN_PLACE=TRUE -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_UNITTESTS=FALSE -DBUILD_BENCHMARKS=FALSE -DENABLE_LTO=FALSE \
    -DENABLE_SOUND=FALSE -DUSE_SDL2_SHARED=TRUE && cmake --build build -j "$BUILD_JOBS"
RUN mkdir -p craftium/luanti && cp -r bin builtin client fonts textures craftium/luanti \
    && cp -r craftium-envs craftium/ \
    && printf 'recursive-include craftium/luanti *\nrecursive-include craftium/craftium-envs *\n' > MANIFEST.in \
    && python -m pip install . 'numpy==2.5.3' 'pillow==11.3.0' 'gymnasium==0.29.1' 'pygame==2.6.1' 'PyYAML==6.0.3' 'cloudpickle==3.1.2' 'Farama-Notifications==0.0.6' 'typing_extensions==4.16.0'
WORKDIR /tmp
ENV LIBGL_ALWAYS_SOFTWARE=1 SDL_AUDIODRIVER=dummy PYTHONHASHSEED=0
ENV SDL_VIDEODRIVER=offscreen LP_NUM_THREADS=1
LABEL org.generalgamebench.engine-revision="8cffe4176e793f78d00b17fa7e46ccf333a7b5b0"
LABEL org.generalgamebench.variant="serial-lockstep-v2"
ENTRYPOINT ["python", "-u"]
