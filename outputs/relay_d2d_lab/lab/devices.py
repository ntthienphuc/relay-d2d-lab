"""Device registration and control. This is a trusted, local laboratory protocol."""
import ipaddress
import time

FIELDS = ('model', 'role', 'local_ip', 'listen_port', 'pending_events', 'running',
          'version', 'control_version', 'platform', 'bridge_id', 'ap_ip', 'ssid',
          'rssi_dbm', 'queue_lost', 'session', 'capabilities', 'paused', 'tx_dbm',
          'wifi_connected','uptime_ms','flash_bytes','psram_bytes','reset_reason',
          'received','forwarded','acks','invalid','send_errors','heap_free','wifi_ssid','wifi_frequency_mhz',
          'battery_percent','management_ok','target_ip','target_port','ap_clients','channel','last_disconnect_reason')


def register(devices, data, endpoint=None):
    key = data.get('id')
    if not isinstance(key, str) or not key or len(key) > 64:
        raise ValueError('Invalid device ID')
    if data.get('role') not in ('source', 'relay', 'sink'):
        raise ValueError('Invalid device role')
    if data.get('role') == 'relay' and data.get('platform') != 'esp32':
        raise ValueError('Trạm chuyển tiếp phải là ESP32.')
    if not isinstance(data.get('listen_port'), int) or not 1024 <= data['listen_port'] <= 65535:
        raise ValueError('Invalid device UDP port')
    ipaddress.IPv4Address(data.get('local_ip', '0.0.0.0'))
    old = devices.setdefault(key, {})
    session_changed = old.get('session') != data.get('session')
    if session_changed:
        old.pop('endpoint', None)
    old.update({k: data[k] for k in FIELDS if k in data})
    old['id'] = key
    old['http_seen' if endpoint is None else 'last_seen'] = time.time()
    if endpoint is not None:
        old['endpoint'] = list(endpoint)
    return old


def endpoint(devices, key):
    d = devices.get(key, {})
    if not d.get('running', False) or time.time() - d.get('last_seen', 0) > 8 or 'endpoint' not in d:
        raise ValueError('Thiết bị chưa online hoặc thiếu UDP HELLO: ' + key)
    return tuple(d['endpoint'])


def control_update(engine, key, **changes):
    old = engine.controls.get(key, {})
    # A running phone may still remember commands from a previous PC process.
    remembered = engine.devices.get(key, {}).get('control_version', -1)
    control = {**old, **changes, 'version': max(old.get('version', 0), remembered) + 1}
    engine.controls[key] = control
    return control['version']
