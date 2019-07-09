import json
import polling
import requests

OK_RESPONSE = 200

config_path = './config.json'
with open(config_path, 'r') as f_config:
    config = json.load(f_config)


def probe(services: dict, request_timeout: float):
    probe_result = {}

    for model, url in services.items():
        service_name = ' '.join([model, url])
        try:
            response = requests.post(f'{url}/poller', json={}, timeout=request_timeout)
            probe_result[service_name] = response.status_code is OK_RESPONSE
        except Exception:
            probe_result[service_name] = False

    return probe_result


def act(services_status: dict, probe_result: dict):
    urls = {url: probe_result[url] for url, status in services_status.items() if (url in probe_result and
                                                                                  status is not probe_result[url])}
    if urls:
        notify(urls)


def notify(services: dict, first_notification=False):
    channel = config['general']['notification']
    channel_config = config['notification'][channel]
    msgs = config['notification']
    launch_msg = msgs['launch_msg']
    up_msg = msgs['up_msg']
    down_msg = msgs['down_msg']

    up_services = '\n'.join([service for service, status in services.items() if status])
    down_services = '\n'.join([service for service, status in services.items() if not status])
    notification = []
    if first_notification:
        notification.append(f'{launch_msg}')
    if up_services:
        notification.append(f'{up_msg}\n\n{up_services}')
    if down_services:
        notification.append(f'{down_msg}\n\n{down_services}')
    notification = '\n\n'.join(notification)

    if channel == 'slack':
        webhook = channel_config['webhook']
        payload = {'text': notification}
        _ = requests.post(webhook, json=payload)


def start_pooling():
    polling_interval = config['general']['polling_interval']
    request_timeout = config['general']['request_timeout']
    services = config['services']

    services_status = probe(services, request_timeout)
    notify(services_status, True)

    def estimate(prob: dict):
        return services_status != prob

    while True:
        probe_result = polling.poll(
            lambda: probe(services, request_timeout),
            check_success=estimate,
            step=polling_interval,
            poll_forever=True)

        act(services_status, probe_result)
        services_status = probe_result


if __name__ == '__main__':
    start_pooling()
