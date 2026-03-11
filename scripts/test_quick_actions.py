import urllib.request, json
msgs = ['Admission Info','Hostel Details','Canteen','Exam Dates']
for msg in msgs:
    req = urllib.request.Request('http://127.0.0.1:8000/process_message/', data=json.dumps({'message': msg}).encode('utf-8'), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode('utf-8')
            print('---', msg, '---')
            print('status', resp.status)
            print(body)
    except Exception as e:
        print('---', msg, '---')
        print('ERROR:', e)
