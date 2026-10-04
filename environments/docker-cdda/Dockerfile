FROM python:3.12-slim-bookworm@sha256:54c85f3c47607a77f32adec749d3c81d1348bf25833671f512b26a9b6d778cb3
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends g++ cmake ninja-build pkg-config libsdl2-dev libsdl2-image-dev libsdl2-ttf-dev zlib1g-dev libfreetype6-dev gettext libgl1-mesa-dri ca-certificates && rm -rf /var/lib/apt/lists/*
RUN python -m pip install pillow==11.3.0 numpy==1.26.4
COPY . /source
WORKDIR /source
RUN cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS_RELEASE='-O1 -DNDEBUG' -DTILES=ON -DCURSES=OFF -DSOUND=OFF -DTESTS=OFF -DLOCALIZE=OFF -DBACKTRACE=OFF -DUSE_PREFIX_DATA_DIR=OFF && cmake --build build -j 6
ENV SDL_VIDEODRIVER=offscreen SDL_AUDIODRIVER=dummy LIBGL_ALWAYS_SOFTWARE=1 LP_NUM_THREADS=1
WORKDIR /tmp
LABEL org.generalgamebench.engine-revision="7b2efa5cea38e4d4d97dd0e63b28b9148623da59"
LABEL org.generalgamebench.variant="native-lockstep-v1"
ENTRYPOINT ["python", "-u"]
