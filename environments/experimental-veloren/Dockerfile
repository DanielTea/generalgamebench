FROM python:3.12-slim-trixie@sha256:02108f5d322dd89f1c9e552442c25acb0543dfdbc455693a5599624f20d9155d
ENV DEBIAN_FRONTEND=noninteractive RUSTUP_HOME=/opt/rustup CARGO_HOME=/opt/cargo PATH=/opt/cargo/bin:$PATH
RUN apt-get update && apt-get install -y --no-install-recommends rustup g++ cmake make pkg-config git ca-certificates libasound2-dev libudev-dev libx11-dev libxrandr-dev libxi-dev libxcursor-dev libxkbcommon-dev libxkbcommon-x11-0 libssl-dev libfontconfig1-dev libfreetype6-dev libvulkan1 mesa-vulkan-drivers libgl1-mesa-dri xvfb xauth && rm -rf /var/lib/apt/lists/*
RUN rustup toolchain install nightly-2026-06-13 --profile minimal
RUN apt-get update && apt-get install -y --no-install-recommends mold && rm -rf /var/lib/apt/lists/*
COPY . /source
WORKDIR /source
RUN --mount=type=cache,id=ggbench-veloren-target,target=/source/target --mount=type=cache,id=ggbench-veloren-registry,target=/opt/cargo/registry --mount=type=cache,id=ggbench-veloren-git,target=/opt/cargo/git VELOREN_GIT_VERSION=/f6294887/1791135206 VELOREN_ASSETS=/source/assets CARGO_INCREMENTAL=0 cargo +nightly-2026-06-13 build --locked -j 3 -p veloren-voxygen --no-default-features --features singleplayer,shaderc-from-source && mkdir -p /engine && cp target/debug/veloren-voxygen /engine/
ENV LIBGL_ALWAYS_SOFTWARE=1 LP_NUM_THREADS=1 VELOREN_ASSETS=/source/assets
ENTRYPOINT ["/engine/veloren-voxygen"]
