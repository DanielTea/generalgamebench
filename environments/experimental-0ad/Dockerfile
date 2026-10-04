FROM python:3.12-slim-trixie@sha256:02108f5d322dd89f1c9e552442c25acb0543dfdbc455693a5599624f20d9155d
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends g++ make cmake patch pkg-config curl ca-certificates zlib1g-dev libboost-dev libboost-filesystem-dev libenet-dev libfmt-dev libfreetype6-dev libicu-dev libcurl4-openssl-dev libpng-dev libsodium-dev libxml2-dev libsdl2-dev libmozjs-128-dev libgl1-mesa-dev libgl1-mesa-dri libx11-dev libxrandr-dev libnvtt-dev xvfb xauth && rm -rf /var/lib/apt/lists/*
RUN python -m pip install pillow==11.3.0 numpy==1.26.4
RUN apt-get update && apt-get install -y --no-install-recommends xz-utils libgloox-dev && rm -rf /var/lib/apt/lists/*
COPY . /source
WORKDIR /source
RUN libraries/build-source-libs.sh --with-system-mozjs -j6
RUN --mount=type=cache,id=ggbench-0ad-compile,target=/source/build/workspaces/gcc build/workspaces/update-workspaces.sh --with-system-mozjs --without-atlas --without-audio --without-lobby --without-miniupnpc --without-dap-interface --without-tests && make -C build/workspaces/gcc config=release -j6
ENV SDL_AUDIODRIVER=dummy LIBGL_ALWAYS_SOFTWARE=1 LP_NUM_THREADS=1
ENTRYPOINT ["python", "-u"]
