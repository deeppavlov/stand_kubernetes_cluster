ARG BASE_IMAGE
FROM $BASE_IMAGE

CMD gunicorn --workers=1 --bind 0.0.0.0:8004 --timeout=300 server:app
