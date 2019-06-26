import json
import polling
import requests


config_path = './config.json'
with open(config_path, 'r') as f_config:
    config = json.load(f_config)


def probe(stands: dict, request_timeout: float, response_pattern: int):
    probe_result = {}

    for url, model in stands.items():
        stand_name = ' '.join([model, url])
        try:
            response = requests.post(url+'/poller', json={}, timeout=request_timeout)
            probe_result[stand_name] = response.status_code == response_pattern
        except Exception:
            probe_result[stand_name] = False

    return probe_result


def act(stands_status: dict, probe_result: dict):
    urls = {url: probe_result[url] for url, status in stands_status.items() if (url in probe_result and
                                                                                status is not probe_result[url])}
    if urls:
        notify(urls)


def notify(stands: dict, first_notification=False):
    channel = config['general']['notification']
    channel_config = config['notification'][channel]

    good_stands = '\n'.join([stand for stand, status in stands.items() if status])
    bad_stands = '\n'.join([stand for stand, status in stands.items() if not status])
    notification = []
    if first_notification:
        notification.append('THIS IS FIRST NOTIFICATION AFTER LAUNCH.')
    if good_stands:
        notification.append(f'Following stand endpoints are reachable:\n\n{good_stands}')
    if bad_stands:
        notification.append(f'Following stand endpoints are unreachable:\n\n{bad_stands}')
    notification = '\n\n'.join(notification)

    if channel == 'slack':
        webhook = channel_config['webhook']
        payload = {'text': notification}
        _ = requests.post(webhook, json=payload)


def start_pooling():
    polling_interval = config['general']['polling_interval']
    request_timeout = config['general']['request_timeout']
    response_pattern = config['general']['response_pattern']
    stands = config['stands']

    stands_status = probe(stands, request_timeout, response_pattern)
    notify(stands_status, True)

    def estimate(prob: dict):
        return stands_status != prob

    while True:
        probe_result = polling.poll(
            lambda: probe(stands, request_timeout, response_pattern),
            check_success=estimate,
            step=polling_interval,
            poll_forever=True)

        act(stands_status, probe_result)
        stands_status = probe_result


if __name__ == '__main__':
    start_pooling()
