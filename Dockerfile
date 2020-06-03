FROM    python:alpine3.10

ENV     HOME=/app
ENV     PYTHONPATH=${HOME}
ENV     PYTHONUNBUFFERED=true
ENV     LIBRARY_PATH=/lib:/usr/lib

WORKDIR ${HOME}

RUN     apk add --update-cache build-base pango-dev cairo-dev libffi-dev libxml2-dev libxslt-dev jpeg-dev zlib-dev ttf-dejavu uwsgi uwsgi-python3 musl-dev gdk-pixbuf-dev
RUN     chown -R guest:users ${HOME}

USER    guest

COPY    ./pod/requirements.txt ${HOME}/pod/

RUN     pip3 install --user -r ${HOME}/pod/requirements.txt

COPY    ./uwsgi-config.ini ${HOME}/pod.ini
COPY    ./pod/ ${HOME}/pod/

CMD     ["sh", "-c", "uwsgi --ini ${HOME}/pod.ini"]
