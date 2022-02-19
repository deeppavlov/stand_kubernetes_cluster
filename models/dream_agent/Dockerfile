ARG BASE_IMAGE
FROM $BASE_IMAGE

CMD sh -c 'bin/wait && python -m deeppavlov_agent.run -ch http_client -pl assistant_dists/dream/pipeline_conf.json --cors'
