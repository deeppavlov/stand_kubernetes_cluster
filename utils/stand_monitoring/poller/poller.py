import json
import requests
import time
from pathlib import Path
from requests.exceptions import ConnectionError, ReadTimeout
from typing import Dict, List, Optional

import polling

OK_RESPONSE = 200

config_path = Path(__file__).resolve().parent / 'config.json'
with open(config_path, 'r') as f_config:
    config = json.load(f_config)


def probe(services: Dict[str, str], request_timeout: float) -> Dict[str, bool]:
    probe_result = dict()

    for model, url in services.items():
        service_name = ' '.join([model, url])
        probe_result[service_name] = custom_post(f'{url}/poller', timeout=request_timeout)

    return probe_result


def custom_post(url: str, payload: Optional[Dict] = None, timeout: float = None) -> bool:
    if payload is None:
        payload = dict()
    start_time = time.time()
    while True:
        try:
            response = requests.post(url, json=payload, timeout=timeout)
            return response.status_code is OK_RESPONSE
        except ReadTimeout:
            return False
        except ConnectionError:
            if time.time() - start_time < timeout:
                time.sleep(1.0)
            else:
                return False


def act(services_status: Dict[str, bool], probe_result: Dict[str, bool]) -> None:
    changed_status = {url: probe_result[url] for url, status in services_status.items() if (url in probe_result and
                                                                                            status is not probe_result[url])}
    still_unreachable = [url for url, status in probe_result.items() if (status is False and url not in changed_status)]
    if changed_status:
        notify(changed_status, still_unreachable=still_unreachable)


def notify(services: Dict[str, bool], still_unreachable: List[str] = None, first_notification: bool = False) -> None:
    channel = config['general']['notification']
    channel_config = config['notification'][channel]
    msgs = config['notification']
    launch_msg = msgs['launch_msg']
    up_msg = msgs['up_msg']
    down_msg = msgs['down_msg']
    unreachable_msg = msgs['unreachable_msg']
    all_up = msgs['all_up_msg']

    up_services = '\n'.join([service for service, status in services.items() if status])
    down_services = '\n'.join([service for service, status in services.items() if not status])
    notification = []
    if first_notification:
        notification.append(f'{launch_msg}')
    if up_services:
        notification.append(f'{up_msg}\n{up_services}')
    if down_services:
        notification.append(f'{down_msg}\n{down_services}')
    if still_unreachable:
        unreachable_services = '\n'.join(still_unreachable)
        notification.append(f'{unreachable_msg}\n{unreachable_services}')
    if not down_services and not still_unreachable:
        notification.append(all_up)
    notification = '\n\n'.join(notification)

    if channel == 'slack':
        webhook = channel_config['webhook']
        payload = {'text': notification}
        _ = custom_post(webhook, payload=payload)


def start_pooling() -> None:
    polling_interval = config['general']['polling_interval']
    request_timeout = config['general']['request_timeout']
    services = config['services']

    services_status = probe(services, request_timeout)
    notify(services_status, first_notification=True)

    def estimate(prob: Dict[str, bool]) -> bool:
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
