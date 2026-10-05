FROM python:3.12-slim-bookworm@sha256:54c85f3c47607a77f32adec749d3c81d1348bf25833671f512b26a9b6d778cb3
ARG BUILD_JOBS=2
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends cmake make g++ pkg-config libogg-dev libvorbis-dev libopenal-dev libboost-filesystem-dev libboost-date-time-dev libsdl2-dev libsdl2-image-dev libfreetype6-dev libraqm-dev libcurl4-openssl-dev libglew-dev libharfbuzz-dev libfribidi-dev libglm-dev zlib1g-dev gettext && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y --no-install-recommends libboost-locale-dev && rm -rf /var/lib/apt/lists/*
COPY . /source
WORKDIR /source
RUN cmake -B build -DCMAKE_BUILD_TYPE=Release -DENABLE_DISCORD=OFF -DBUILD_TESTING=OFF && cmake --build build -j "$BUILD_JOBS"
RUN python -m pip install pillow==11.3.0 numpy==1.26.4
ENV SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy SDL_RENDER_DRIVER=software
WORKDIR /tmp
LABEL org.generalgamebench.engine-revision="c1ddb4f28c54de77f07aa9965231a91c0ed06708"
LABEL org.generalgamebench.variant="native-lockstep-v1"
ENTRYPOINT ["python", "-u"]
