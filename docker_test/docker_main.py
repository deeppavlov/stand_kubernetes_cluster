import docker
import nvidia_smi
import requests

nvidia_smi.nvmlInit()
client = docker.from_env()
handle = nvidia_smi.nvmlDeviceGetHandleByIndex(0)



def interact(config):
    log = []
    try:
        client.containers.run('ngc-image', environment=[f'CONFIG={config}'], detach=True, name='ngc-test', remove=True,
                              ports={'5000/tcp': 5000})
        container = client.containers.get('ngc-test')
        for line in container.logs(stream=True):
            log.append(line.decode())
            print(line.decode(), end='')
            if 'Uvicorn running on http://0.0.0.0:5000' in line.decode():
                get_response = requests.get('http://0.0.0.0:5000/api')
                response_code = get_response.status_code
                assert response_code == 200
                model_args_names = get_response.json()
                post_payload = dict()
                for arg_name in model_args_names:
                    arg_value = ' '.join(['qwerty'] * 10)
                    post_payload[arg_name] = [arg_value]
                post_response = requests.post('http://0.0.0.0:5000/model',
                                              json=post_payload,
                                              headers={'Accept': 'application/json'})
                response_code = post_response.status_code
                assert response_code == 200

                mem_res = nvidia_smi.nvmlDeviceGetMemoryInfo(handle)
                with open('result.txt', 'a') as file:
                    file.write(f'{config}, {mem_res.used / 1024 ** 2}\n')
                    file.write(f'{post_response.json()}\n')
                container.stop()
        with open(f'{config}.log', 'w') as file:
            file.writelines(log)
    except Exception as e:
        print(e)
        container.stop()


configs = ['bleu_retrieve', 'tfidf_retrieve', 'tfidf_logreg_en_faq', 'tfidf_autofaq', 'tfidf_logreg_autofaq',
           'fasttext_avg_autofaq', 'fasttext_tfidf_autofaq', 'brillmoore_wikitypos_en', 'brillmoore_kartaslov_ru',
           'levenshtein_corrector_ru', 'gobot_dstc2', 'gobot_dstc2_best', 'gobot_dstc2_minimal', 'paraphraser_bert',
           'paraphraser_rubert', 'insults_kaggle_bert', 'insults_kaggle_conv_bert', 'rusentiment_bert',
           'intents_dstc2_bert', 'intents_dstc2', 'intents_dstc2_big', 'insults_kaggle', 'sentiment_twitter',
           'sentiment_twitter_bert_emb', 'sentiment_twitter_preproc', 'topic_ag_news', 'rusentiment_cnn',
           'rusentiment_elmo_twitter_cnn', 'rusentiment_bigru_superconv', 'yahoo_convers_vs_info',
           'ru_obscenity_classifier', 'sentiment_sst_conv_bert', 'sentiment_sst_multi_bert', 'sentiment_yelp_conv_bert',
           'sentiment_yelp_multi_bert', 'sentiment_imdb_bert', 'sentiment_imdb_conv_bert', 'intents_snips',
           'intents_sample_csv', 'intents_sample_json', 'conll2003_m1', 'vlsp2016_full',
           'ner_conll2003_bert', 'ner_ontonotes_bert', 'ner_ontonotes_bert_mult', 'ner_rus_bert', 'ner_conll2003',
           'ner_dstc2', 'ner_ontonotes', 'ner_ontonotes_bert_emb', 'ner_few_shot_ru_simulate', 'ner_rus',
           'slotfill_dstc2', 'sentseg_dailydialog', 'kbqa_rus', 'kbqa_tree', 'kbqa_cq', 'kbqa_cq_bert_ranker',
           'elmo_ru_news', 'elmo_1b_benchmark_test', 'ranking_insurance', 'ranking_insurance_interact',
           'ranking_ubuntu_v2', 'ranking_ubuntu_v2_interact', 'ranking_ubuntu_v2_mt', 'ranking_ubuntu_v2_mt_interact',
           'paraphrase_ident_paraphraser', 'paraphrase_ident_paraphraser_interact',
           'paraphrase_ident_paraphraser_pretrain', 'paraphrase_ident_paraphraser_tune',
           'paraphrase_ident_tune_interact', 'paraphrase_ident_paraphraser_elmo', 'paraphrase_ident_elmo_interact',
           'paraphrase_ident_qqp', 'paraphrase_ident_qqp_bilstm_interact', 'paraphrase_ident_qqp_bilstm',
           'paraphrase_ident_qqp_interact', 'ranking_ubuntu_v2_bert_uncased', 'ranking_ubuntu_v2_bert_sep',
           'ranking_ubuntu_v2_bert_sep_interact', 'ranking_ubuntu_v1_mt_word2vec_smn',
           'ranking_ubuntu_v1_mt_word2vec_dam', 'ranking_ubuntu_v1_mt_word2vec_dam_transformer',
           'ranking_ubuntu_v2_mt_word2vec_smn', 'ranking_ubuntu_v2_mt_word2vec_dam',
           'ranking_ubuntu_v2_mt_word2vec_dam_transformer', 'ranking_ubuntu_v2_mt_word2vec_dam_transformer',
           'squad_ru_bert',
           'squad_ru_bert_infer', 'squad_ru_rubert', 'squad_ru_rubert_infer', 'squad_bert', 'squad_bert_infer', 'squad',
           'squad_ru', 'multi_squad_noans', 'squad_zh_bert_mult', 'squad_zh_bert_zh', 'bot_kvret_train', 'bot_kvret',
           'ru_odqa_infer_wiki', 'UD2', 'UD2', 'BERT',
           'syntax_ru_syntagrus_bert', 'ru_syntagrus_joint_parsing']

if __name__ == '__main__':
    interact('bleu_retrieve')
