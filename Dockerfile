FROM alpine:3.22.1 AS builder

RUN apk add --no-cache \
    build-base \
    cmake \
    git \
    python3-dev \
    py3-pip \
    pkgconfig \
    swig \
    json-c-dev \
    linux-headers

# Build mraa from source
WORKDIR /tmp
RUN git clone https://github.com/eclipse/mraa.git && \
    mkdir mraa/build && \
    cd mraa/build && \
    cmake .. \
      -DPYTHON3_INCLUDE_DIR=$(python3 -c "import sysconfig; print(sysconfig.get_path('include'))") \
      -DPYTHON3_LIBRARY=$(python3 -c "import sysconfig; print(sysconfig.get_config_var('LIBDIR'))") \
      -DBUILDSWIGPYTHON=ON \
      -DCMAKE_INSTALL_PREFIX=/usr/local && \
    make -j$(nproc) && \
    make install

FROM alpine:3.22.1

RUN apk add --no-cache \
    python3 \
    json-c

COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/lib/libmraa* /usr/local/lib/
COPY --from=builder /usr/local/include/mraa* /usr/local/include/

RUN ldconfig /usr/local/lib

ENV PYTHONPATH=/usr/local/lib/python3.12/site-packages:$PYTHONPATH

WORKDIR /app
COPY rockpi-poe.py .

ENV POE_LV0=40 \
    POE_LV1=45 \
    POE_LV2=50 \
    POE_LV3=55

RUN adduser -D -u 1000 rockpi
USER rockpi

CMD ["python3", "rockpi-poe.py", "start"]
