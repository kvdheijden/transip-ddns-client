from ddns.provider import DDNSProvider
from ddns.utils import compare_dns

from typing import AnyStr, List, Dict

import requests
import uuid
import json
import base64
import OpenSSL.crypto
import logging


class TransIPProvider(DDNSProvider):
    def __init__(self, login=None, read_only='True', expiration_time='30 minutes', label=None, global_key='False',
                 keyfile=None, test=False, labelfmt='%(label)s-%(nonce)s'):
        self.login = login
        self.read_only = str(read_only) != 'False'
        self.expiration_time = expiration_time
        self.label = label
        self.global_key = str(global_key) == 'True'
        with open(keyfile, 'r') as f:
            key = f.read()
            self.__pkey = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, key)
        self.test = str(test) != 'False'

        self.base = 'https://api.transip.nl/v6'
        self._authorization = None

        self._labelfmt = labelfmt

    @property
    def _auth_token(self):
        if self.test:
            return 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6ImN3MiFSbDU2eDNoUnkjelM4YmdOIn0.eyJpc3MiOiJhcGkudHJhb' \
                   'nNpcC5ubCIsImF1ZCI6ImFwaS50cmFuc2lwLm5sIiwianRpIjoiY3cyIVJsNTZ4M2hSeSN6UzhiZ04iLCJpYXQiOjE1ODIyMD' \
                   'E1NTAsIm5iZiI6MTU4MjIwMTU1MCwiZXhwIjoyMTE4NzQ1NTUwLCJjaWQiOiI2MDQ0OSIsInJvIjpmYWxzZSwiZ2siOmZhbHN' \
                   'lLCJrdiI6dHJ1ZX0.fYBWV4O5WPXxGuWG-vcrFWqmRHBm9yp0PHiYh_oAWxWxCaZX2Rf6WJfc13AxEeZ67-lY0TA2kSaOCp0P' \
                   'ggBb_MGj73t4cH8gdwDJzANVxkiPL1Saqiw2NgZ3IHASJnisUWNnZp8HnrhLLe5ficvb1D9WOUOItmFC2ZgfGObNhlL2y-AMN' \
                   'LT4X7oNgrNTGm-mespo0jD_qH9dK5_evSzS3K8o03gu6p19jxfsnIh8TIVRvNdluYC2wo4qDl5EW5BEZ8OSuJ121ncOT1oRpz' \
                   'XB0cVZ9e5_UVAEr9X3f26_Eomg52-PjrgcRJ_jPIUYbrlo06KjjX2h0fzMr21ZE023Gw'
        else:
            nonce = uuid.uuid1().hex
            label = self._labelfmt % {'label': self.label, 'nonce': nonce, 'expiration_time': self.expiration_time}
            request_body = {
                'login': self.login,
                'nonce': nonce,
                'read_only': self.read_only,
                'expiration_time': self.expiration_time,
                'label': label,
                'global_key': self.global_key
            }
            json_encoded_request_body = json.dumps(request_body)
            signed_request_body = OpenSSL.crypto.sign(self.__pkey, json_encoded_request_body, 'sha512')
            base64_encoded_request_body = base64.b64encode(signed_request_body)
            r = requests.post(f'{self.base}/auth',
                              data=json_encoded_request_body,
                              headers={'Signature': base64_encoded_request_body})

            if r.status_code != 201:
                raise Exception(r.text)

            logging.debug(f'Created new auth token with label {label}')
            return json.loads(r.text)['token']

    @property
    def _headers(self):
        if self._authorization is None:
            self._authorization = self._auth_token
        return {'Authorization': f'Bearer {self._authorization}'}

    def _try_request(self, method, url, data=None, retry=True):
        r = method(f'{self.base}{url}', data=data, headers=self._headers)
        if retry and r.status_code == 401:
            self._authorization = None
            return self._try_request(method, url, data, False)

        return r

    def _get_dns_entries(self, domain: AnyStr) -> List[Dict]:
        r = self._try_request(requests.get, f'/domains/{domain}/dns')

        if r.status_code != 200:
            raise Exception(r.status_code)

        return json.loads(r.text)['dnsEntries']

    def _add_entry(self, domain: AnyStr, entry: Dict, new_ip: AnyStr) -> None:
        dns_entry = dict(entry, content=entry['content'] % {'ip': new_ip})
        r = self._try_request(requests.post, f'/domains/{domain}/dns', json.dumps({
            'dnsEntry': dns_entry
        }))

        if r.status_code != 201:
            raise Exception(r.status_code)

        logging.info(f'Added DNS entry {dns_entry}')

    def _update_entry(self, domain: AnyStr, entry: Dict, new_ip: AnyStr) -> None:
        dns_entry = dict(entry, content=entry['content'] % {'ip': new_ip})
        r = self._try_request(requests.patch, f'/domains/{domain}/dns', json.dumps({
            'dnsEntry': dns_entry
        }))

        if r.status_code != 204:
            raise Exception(r.status_code)

        logging.info(f'Updated DNS entry {dns_entry}')

    def update(self, current_ip: AnyStr, new_ip: AnyStr, domain: AnyStr, dns: List[Dict]) -> None:
        current_dns = self._get_dns_entries(domain)

        for entry in dns:
            current_entry = [e for e in current_dns if compare_dns(entry, e)]

            if not len(current_entry):
                self._add_entry(domain, entry, new_ip)
            else:
                self._update_entry(domain, entry, new_ip)
