import http.client
import json

def sendSMS(to_number, message_text):
    conn = http.client.HTTPSConnection("api.infobip.com")
    payload = json.dumps({
        "messages": [
            {
                "destinations": [{"to": str(to_number)}],
                "from": "RN360 BUS",
                "text": message_text
            }
        ]
    })
    headers = {
        'Authorization': 'App 6e5db2e07847500965018dc1bc46cdfb-cd7e6ba0-372a-4309-91d2-49a6c27ac09d',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    conn.request("POST", "/sms/2/text/advanced", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))