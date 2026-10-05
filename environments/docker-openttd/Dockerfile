FROM python:3.12-slim-bookworm@sha256:54c85f3c47607a77f32adec749d3c81d1348bf25833671f512b26a9b6d778cb3
ARG BUILD_JOBS=2
RUN apt-get update && apt-get install -y --no-install-recommends g++ make cmake pkg-config libsdl2-dev liblzma-dev libpng-dev zlib1g-dev libfreetype6-dev libfontconfig1-dev libicu-dev libharfbuzz-dev openttd-opengfx ca-certificates && rm -rf /var/lib/apt/lists/*
RUN python -m pip install pillow==11.3.0 numpy==1.26.4
COPY . /source
WORKDIR /source
RUN cmake -B build -DCMAKE_BUILD_TYPE=Release -DOPTION_USE_ASSERTS=ON -DOPTION_USE_THREADS=OFF -DOPTION_DEDICATED=OFF && cmake --build build --target openttd -j "$BUILD_JOBS"
RUN cp -r /usr/share/games/openttd/baseset/opengfx /source/build/baseset/
RUN python /source/verify-assets.py
WORKDIR /tmp
LABEL org.generalgamebench.engine-revision="14ec60f248547d4d062a1160f0fc26d742319888"
LABEL org.generalgamebench.variant="native-lockstep-v1"
ENTRYPOINT ["python", "-u"]
