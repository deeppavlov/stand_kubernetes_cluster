import json

import polling
import requests


config_path = './config.json'
with open(config_path, 'r') as f_config:
    config = json.load(f_config)


def probe(urls: dict, response_patterns: dict, request_timeout: float):
    probe_result = {}

    for url, payload in urls.items():
        pattern = response_patterns[url] if url in response_patterns.keys() else response_patterns['default']
        try:
            response = requests.post(url, json=payload, timeout=request_timeout)
            probe_result[url] = response.status_code in pattern
        except Exception:
            probe_result[url] = False

    return probe_result


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
    request_timeout = config['general']['request_timeout']
    urls = config['urls']
    response_patterns = config['response_patterns']

    urls_status = {url: True for url in urls.keys()}

    def estimate(prob: dict):
        return urls_status != prob

    while True:
        probe_result = polling.poll(
            lambda: probe(urls, response_patterns, request_timeout),
            check_success=estimate,
            step=polling_interval,
            poll_forever=True)

        act(urls_status, probe_result)
        urls_status = probe_result


if __name__ == '__main__':
    start_pooling()
