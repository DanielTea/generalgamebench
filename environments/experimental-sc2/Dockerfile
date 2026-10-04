FROM python:3.12-slim-bookworm@sha256:54c85f3c47607a77f32adec749d3c81d1348bf25833671f512b26a9b6d778cb3
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends libosmesa6 libglib2.0-0 libx11-6 libxcursor1 libxrandr2 libxi6 libsm6 libice6 libglew2.2 libsdl2-2.0-0 libfontconfig1 ca-certificates && rm -rf /var/lib/apt/lists/*
RUN python -m pip install s2clientprotocol==5.0.16.97563.0 protobuf==3.20.3 websocket-client==1.9.0 pillow==11.3.0 numpy==1.26.4
ENV LIBGL_ALWAYS_SOFTWARE=1 LP_NUM_THREADS=1
ENTRYPOINT ["python", "-u"]
