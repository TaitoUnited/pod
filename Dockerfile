FROM    python:3.11-alpine

ENV     HOME=/app
ENV     PYTHONUNBUFFERED=true
ENV     PYTHONPATH=${HOME}/pod:${HOME}/.local/lib/python3.11/site-packages
ENV     LIBRARY_PATH=/lib:/usr/lib

WORKDIR ${HOME}

RUN     apk add --update-cache build-base pango-dev cairo-dev libffi-dev libxml2-dev libxslt-dev jpeg-dev zlib-dev ttf-dejavu uwsgi uwsgi-python3 musl-dev gdk-pixbuf-dev font-noto font-noto-emoji font-noto-cjk weasyprint
RUN     chown -R guest:users ${HOME}

USER    guest

COPY    ./pod/requirements.txt ${HOME}/pod/

RUN     pip3 install --user -r ${HOME}/pod/requirements.txt

COPY    ./uwsgi-config.ini ${HOME}/pod.ini
COPY    ./pod/ ${HOME}/pod/

RUN     chmod -R go+rx ${HOME}/.local

CMD     ["sh", "-c", "uwsgi --ini ${HOME}/pod.ini"]