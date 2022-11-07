ARG BASE_IMAGE
FROM $BASE_IMAGE

CMD sh -c 'bin/wait && python -m deeppavlov_agent.run agent.channel=telegram agent.telegram_token=$TG_TOKEN agent.pipeline_config=assistant_dists/dream/pipeline_conf.json agent.db_config=assistant_dists/dream/db_conf.json'
