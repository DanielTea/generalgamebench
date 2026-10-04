FROM python:3.12-slim-bookworm@sha256:54c85f3c47607a77f32adec749d3c81d1348bf25833671f512b26a9b6d778cb3
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends g++ make pkg-config libncursesw5-dev bison flex liblua5.4-dev libsqlite3-dev zlib1g-dev libsdl2-image-dev libsdl2-dev libfreetype6-dev libpng-dev fonts-dejavu-core advancecomp pngcrush libgl1-mesa-dev libgl1-mesa-dri ca-certificates && rm -rf /var/lib/apt/lists/*
RUN python -m pip install PyYAML==6.0.3 pillow==11.3.0 numpy==1.26.4
COPY . /source
WORKDIR /source/crawl-ref/source
RUN make -j 6 TILES=y SOUND= NO_PKGCONFIG=
ENV SDL_VIDEODRIVER=offscreen SDL_AUDIODRIVER=dummy LIBGL_ALWAYS_SOFTWARE=1 LP_NUM_THREADS=1
WORKDIR /tmp
LABEL org.generalgamebench.engine-revision="19cb0921cbcb6463fcedd1bb06636446c50b1905"
LABEL org.generalgamebench.variant="native-lockstep-v1"
ENTRYPOINT ["python", "-u"]
