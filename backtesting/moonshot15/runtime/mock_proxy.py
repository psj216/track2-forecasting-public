"""## Executive summary (read this first)
Internal synthetic proxy validates the literal House request contract without real credentials.
"""
from http.server import BaseHTTPRequestHandler,HTTPServer
import json
import sys
from synthetic import reply
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_POST(self):
        assert self.path=='http://house.test:8000/v1/chat/completions'
        assert self.headers.get('Authorization')=='Bearer synthetic-testing-only'
        assert self.headers.get('Proxy-Authorization')=='Basic dGVzdHVzZXI6dGVzdHBhc3M='
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        assert body['model']=='synthetic-house-contract-test'
        assert body['max_tokens']<=4000 and body['temperature']==0
        assert body['chat_template_kwargs']['enable_thinking'] is False
        prompt=body['messages'][0]['content'];ctx=json.loads(prompt.split('\nCONTEXT_JSON\n',1)[1])
        kind=next(k for k in ['E1','E2','A','B','C','D'] if ('M15-E stage'+k[1:] in prompt if k.startswith('E') else 'M15-'+k+':' in prompt))
        payload={'choices':[{'finish_reason':'stop','message':{'content':json.dumps(reply(kind,ctx))}}]}
        raw=json.dumps(payload).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
HTTPServer(('0.0.0.0',8080),Handler).serve_forever()
