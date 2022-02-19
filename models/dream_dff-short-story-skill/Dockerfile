ARG BASE_IMAGE
FROM $BASE_IMAGE

CMD gunicorn --workers=1 server:app -b 0.0.0.0:8057 --reload
