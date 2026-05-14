FROM python:3.14.5-alpine3.22@sha256:6b91e66ab2a880ce9ca5a1b91c70f45963ff71ff68268df056336e1a657d5efd AS base

FROM base AS compiler

WORKDIR /app

COPY src .

RUN python3 -m compileall -b -f . && \
    find . -name "*.py" -type f -delete

FROM base AS dep_installer

WORKDIR /tmp

COPY requirements.txt .

RUN apk add --no-cache build-base cmake git linux-headers swig && \
    pip install --upgrade pip wheel && \
    pip install -r requirements.txt && \
    pip uninstall -y pip wheel && \
    git clone https://github.com/eclipse/mraa.git && \
    mkdir mraa/build && \
    cd mraa/build && \
    cmake .. \
      -DBUILDSWIG=ON \
      -DBUILDSWIGPYTHON=ON \
      -DINSTALLTOOLS=OFF \
      -DENABLEEXAMPLES=OFF \
      -DBUILDTESTS=OFF \
      -DJSONPLAT=OFF \
      -DUSEPYTHON3TESTS=OFF && \
    make -j$(nproc) && \
    make install && \
    apk del build-base git cmake linux-headers swig && \
    cd $(python3 -c "import sysconfig; print(sysconfig.get_paths()['stdlib'])") && \
    mv dist-packages/* site-packages/ && \
    python3 -m compileall -b -f site-packages/ && \
    find site-packages/ -name "*.py" -type f -delete && \
    find . -name "__pycache__" -type d -exec rm -rf {} +

FROM base

COPY --from=dep_installer /usr/local /usr/local

RUN apk add --no-cache libstdc++ && \
    ldconfig /usr/local/lib

WORKDIR /app

COPY --from=compiler /app .

ENTRYPOINT ["python3", "-u", "main.pyc", "start"]
