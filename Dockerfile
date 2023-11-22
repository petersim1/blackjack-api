FROM ubuntu:20.04

RUN apt update
RUN apt install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt install -y python3.11 curl ffmpeg python3-distutils python3-apt build-essential git
RUN curl -sSL https://install.python-poetry.org | (python3.11 - || (cat /*.log && exit 100))
ENV PATH /root/.local/bin:$PATH
ENV PYTHONPATH /app/app

ADD . /app
WORKDIR /app
RUN poetry env use python3.11
RUN poetry install
RUN apt-get purge -y software-properties-common && \
    apt-get clean autoclean && \
    apt-get autoremove --yes && \
    rm -rf /var/lib/{apt,dpkg,cache,log}/
CMD ["make", "run"]