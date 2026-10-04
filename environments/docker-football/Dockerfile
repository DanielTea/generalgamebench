FROM ubuntu:22.04@sha256:5ec03bb3441e8b0bf3b4f9cd4629a1ae763010dc3035bb8da3ae6cf026486401
ENV DEBIAN_FRONTEND=noninteractive PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-dev python3-pip cmake build-essential \
    libgl1-mesa-dev libegl1-mesa-dev libsdl2-dev libsdl2-image-dev \
    libsdl2-ttf-dev libsdl2-gfx-dev libboost-python-dev libboost-system-dev \
    libboost-filesystem-dev libboost-thread-dev libboost-regex-dev \
    libgl1-mesa-dri xvfb xauth ca-certificates && rm -rf /var/lib/apt/lists/*
RUN python3 -m pip install 'pip==24.3.1' 'setuptools==69.5.1' 'wheel==0.45.1' \
    'psutil==6.1.1' 'numpy==1.26.4' 'pillow==11.3.0' 'gym==0.23.1' \
    'opencv-python==4.10.0.84' 'pygame==2.6.1' 'scipy==1.15.3' 'absl-py==2.3.1'
COPY . /source
WORKDIR /source
RUN python3 -m pip install --no-deps --no-build-isolation .
RUN python3 -m pip install 'six==1.17.0'
LABEL org.generalgamebench.engine-revision="ba9952130898bde2879b01ff2b49d3d48d26ce81"
WORKDIR /work
ENV LIBGL_ALWAYS_SOFTWARE=1 SDL_AUDIODRIVER=dummy PYTHONHASHSEED=0
ENTRYPOINT ["python3", "-u"]
