FROM    python:alpine3.10

ENV     HOME=/app
ENV     PYTHONPATH=${HOME}
ENV     PYTHONUNBUFFERED=true
ENV     LIBRARY_PATH=/lib:/usr/lib

WORKDIR ${HOME}

RUN     apk add --update-cache build-base pango-dev cairo-dev libffi-dev libxml2-dev libxslt-dev jpeg-dev zlib-dev ttf-dejavu

COPY    ./pod/requirements.txt ${HOME}/pod/

RUN     pip3 install -r ${HOME}/pod/requirements.txt

COPY    ./pod/ ${HOME}/pod/

CMD     ["python3", "-m", "pod"]
