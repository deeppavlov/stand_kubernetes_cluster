import json

import polling
import requests
from requests import Response


config_path = './config.json'
with open(config_path, 'r') as f_config:
    config = json.load(f_config)


def probe(urls: dict, payload: dict, response_patterns: dict):
    probe_result = {}
    urls_post = urls['post']
    urls_get = urls['get']

    for payload_type, urls_list in urls_post.items():
        for url in urls_list:
            pattern = response_patterns[url] if url in response_patterns.keys() else response_patterns['default']
            try:
                response = requests.post(url, json=payload[payload_type])
                probe_result[url] = assert_response(response, pattern)
            except Exception:
                probe_result[url] = False

    for url in urls_get:
        pattern = response_patterns[url] if url in response_patterns.keys() else response_patterns['default']
        try:
            response = requests.get(url)
            probe_result[url] = assert_response(response, pattern)
        except Exception:
            probe_result[url] = False

    return probe_result


def assert_response(response: Response, pattern: dict):
    if 'code' in pattern.keys():
        if pattern['code'] != response.status_code:
            return False

    return True


def act(urls_status: dict, probe_result: dict):
    bad_urls = [url for url, status in urls_status.items() if url in probe_result and status and not probe_result[url]]
    if bad_urls:
        notify(bad_urls)


def notify(bad_urls: list):
    channel = config['general']['notification']
    channel_config = config['notification'][channel]

    bad_urls_str = '\n'.join(bad_urls)
    notification = f'Following stand endpoints are unreachable:\n\n{bad_urls_str}'

    if channel == 'slack':
        webhook = channel_config['webhook']
        channel_notification = f'@channel {notification}'
        payload = {'text': channel_notification}
        _ = requests.post(webhook, json=payload)


def start_pooling():
    polling_interval = config['general']['polling_interval']
    urls = config['urls']
    payload = config['payload']
    response_patterns = config['response_patterns']

    urls_status = probe(urls, payload, response_patterns)

    def estimate(prob: dict):
        return urls_status != prob

    while True:
        probe_result = polling.poll(
            lambda: probe(urls, payload, response_patterns),
            check_success=estimate,
            step=polling_interval,
            poll_forever=True)

        act(urls_status, probe_result)
        urls_status = probe_result


if __name__ == '__main__':
    start_pooling()
