ARG BASE_IMAGE
FROM $BASE_IMAGE

CMD gunicorn  --workers=1 --timeout 500 server:app -b 0.0.0.0:9075
