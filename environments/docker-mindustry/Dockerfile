FROM python:3.12-slim-bookworm@sha256:54c85f3c47607a77f32adec749d3c81d1348bf25833671f512b26a9b6d778cb3
RUN apt-get update && apt-get install -y --no-install-recommends openjdk-17-jdk-headless g++ libsdl2-dev libglew-dev libgl1-mesa-dri libasound2 xvfb xauth ca-certificates && rm -rf /var/lib/apt/lists/*
RUN python -m pip install pillow==11.3.0 numpy==1.26.4
COPY . /build
WORKDIR /build
RUN mkdir -p /engine /control/classes && cp Mindustry.jar /engine/Mindustry.jar && cp -r arc/backends/backend-sdl/src /build/src
RUN javac -cp jnigen.jar Generate.java && java -cp '/build/*:/build' Generate
RUN g++ -shared -O2 -fPIC -I/usr/lib/jvm/java-17-openjdk-arm64/include -I/usr/lib/jvm/java-17-openjdk-arm64/include/linux -I/usr/include/SDL2 -I/build/native /build/native/*.cpp -lSDL2 -lGLEW -lGL -o /engine/libsdl-arcarm64.so
WORKDIR /engine
RUN jar uf Mindustry.jar libsdl-arcarm64.so
RUN javac -cp /engine/Mindustry.jar -d /control/classes /build/arc/backends/backend-sdl/src/arc/backend/sdl/SdlGraphics.java /build/arc/arc-core/src/arc/util/Time.java /build/BenchmarkLauncher.java
WORKDIR /tmp
ENV SDL_VIDEODRIVER=x11 LIBGL_ALWAYS_SOFTWARE=1 LP_NUM_THREADS=1 ALSOFT_DRIVERS=null
LABEL org.generalgamebench.engine-revision="067c720a8817c1c9fb586c03898a7d948caaed56"
LABEL org.generalgamebench.variant="native-lockstep-v1"
ENTRYPOINT ["python", "-u"]
