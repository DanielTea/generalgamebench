FROM python:3.12-slim-trixie@sha256:02108f5d322dd89f1c9e552442c25acb0543dfdbc455693a5599624f20d9155d
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends g++ cmake ninja-build pkg-config zip gettext ca-certificates libphysfs-dev libpng-dev libjpeg62-turbo-dev libtheora-dev libvorbis-dev libogg-dev libopus-dev libfreetype6-dev libharfbuzz-dev libfribidi-dev libopenal-dev libcurl4-openssl-dev libsodium-dev libsqlite3-dev libzip-dev libgl1-mesa-dev libegl-dev libgl1-mesa-dri libx11-dev libxext-dev libxrandr-dev libxcursor-dev libxi-dev libxfixes-dev libxss-dev libxtst-dev xvfb xauth && rm -rf /var/lib/apt/lists/*
RUN python -m pip install pillow==11.3.0 numpy==1.26.4
COPY SDL3.tar.gz /tmp/SDL3.tar.gz
RUN tar xf /tmp/SDL3.tar.gz -C /tmp && cmake -S /tmp/SDL3-3.2.26 -B /tmp/sdlbuild -G Ninja -DCMAKE_BUILD_TYPE=Release -DSDL_TESTS=OFF -DSDL_EXAMPLES=OFF -DSDL_UNIX_CONSOLE_BUILD=ON && cmake --build /tmp/sdlbuild -j 6 && cmake --install /tmp/sdlbuild && ldconfig && rm -rf /tmp/sdlbuild /tmp/SDL3-3.2.26 /tmp/SDL3.tar.gz
COPY . /source
WORKDIR /source
RUN cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DWZ_ENABLE_WARNINGS_AS_ERRORS=OFF -DWZ_ENABLE_BACKEND_VULKAN=OFF -DWZ_ENABLE_BASIS_UNIVERSAL=OFF -DENABLE_GNS_NETWORK_BACKEND=OFF -DENABLE_DOCS=OFF -DENABLE_NLS=OFF && cmake --build build -j 6
ENV SDL_AUDIODRIVER=dummy LIBGL_ALWAYS_SOFTWARE=1 LP_NUM_THREADS=1
WORKDIR /tmp
LABEL org.generalgamebench.engine-revision="7d3d8e51a61ceee89e6bf672a41337e1a9cd7392"
LABEL org.generalgamebench.variant="native-lockstep-v1"
ENTRYPOINT ["python", "-u"]
