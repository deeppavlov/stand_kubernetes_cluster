ARG BASE_IMAGE
FROM $BASE_IMAGE

CMD sh -c 'agent/bin/wait && uvicorn agent.server:app --host 0.0.0.0 --port $PORT --reload'
