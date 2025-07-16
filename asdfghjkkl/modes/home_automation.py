import requests
import json

def handle_automation(user_input, config):
    # Simple keyword mapping for demo
    if 'turn on' in user_input.lower():
        device = extract_device(user_input)
        return turn_on_device(device, config)
    elif 'turn off' in user_input.lower():
        device = extract_device(user_input)
        return turn_off_device(device, config)
    else:
        return "[Could not map command to device]"

def extract_device(user_input):
    # Very basic extraction for demo
    words = user_input.lower().split()
    for w in words:
        if w in ['light', 'fan', 'lamp', 'plug']:
            return w
    return 'device'

def turn_on_device(device, config):
    if config['home_automation']['backend'] == 'home_assistant':
        return ha_service_call(device, 'turn_on', config)
    elif config['home_automation']['backend'] == 'mqtt':
        return mqtt_publish(device, 'ON', config)
    else:
        return '[No backend configured]'

def turn_off_device(device, config):
    if config['home_automation']['backend'] == 'home_assistant':
        return ha_service_call(device, 'turn_off', config)
    elif config['home_automation']['backend'] == 'mqtt':
        return mqtt_publish(device, 'OFF', config)
    else:
        return '[No backend configured]'

def ha_service_call(device, action, config):
    url = config['home_automation']['ha_url']
    token = config['home_automation']['ha_token']
    entity_id = f"switch.{device}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "entity_id": entity_id
    }
    try:
        r = requests.post(f"{url}/api/services/switch/{action}", headers=headers, json=data, timeout=10)
        r.raise_for_status()
        return f"[{device.title()} {action.replace('_', ' ')} command sent]"
    except Exception as e:
        return f"[Home Assistant error: {e}]"

def mqtt_publish(device, state, config):
    try:
        import paho.mqtt.publish as publish
        topic = config['home_automation']['mqtt_topic_prefix'] + device
        publish.single(topic, state, hostname=config['home_automation']['mqtt_broker'])
        return f"[MQTT: {device} set to {state}]"
    except Exception as e:
        return f"[MQTT error: {e}]"

# Placeholder for future voice input expansion
# def handle_voice_input(...):
#     pass 