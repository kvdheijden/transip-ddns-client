import requests
import uuid
import json
import base64
import OpenSSL.crypto
import logging
from typing import AnyStr, List, Dict, Callable, Optional


class TransIPException(BaseException):
    def __init__(self, status_code: int, error: AnyStr):
        self.status_code = status_code
        self.error = error

        self._status_codes = {
            200: 'OK',
            201: 'Created',
            204: 'No content',

            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not Found',
            405: 'Method Not Allowed',
            406: 'Not Acceptable',
            408: 'Request Timeout',
            409: 'Conflict',
            422: 'Unprocessable Entity',
            429: 'Too Many Requests',
            500: 'Internal Server Error',
            501: 'Not Implemented',
        }

    def __str__(self) -> AnyStr:
        return f'{self.status_code}: {self._status_codes[self.status_code]} - {self.error}'


class TransIPApi(object):
    def __init__(self, domain: AnyStr, test: bool = False, login: AnyStr = None, label: AnyStr = None,
                 expiration_time: AnyStr = '30 minutes', global_key: bool = False,
                 keyfile: AnyStr = '/etc/transipddnsclient/key.pem'):
        self.domain = domain
        self.test = test
        if not self.test:
            if login is None:
                raise ValueError('login is required if test is False')
            self.login = login

            if label is None:
                raise ValueError('label is required if test is False')

            self.label = label
            self.expiration_time = expiration_time
            self.global_key = global_key
            with open(keyfile, 'r') as f:
                key = f.read()
                self.__pkey = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, key)

        self.api = 'https://api.transip.nl/v6'
        self._authorization = None

    @staticmethod
    def compare_dns(a: Dict, b: Dict) -> bool:
        return a['name'] == b['name'] and a['type'] == b['type']

    def _get_authorization(self) -> AnyStr:
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
            request_body = {
                'login': self.login,
                'nonce': nonce,
                'read_only': False,
                'expiration_time': self.expiration_time,
                'label': f'{self.label}_{nonce}',
                'global_key': self.global_key
            }
            json_encoded_request_body = json.dumps(request_body)
            signed_request_body = OpenSSL.crypto.sign(self.__pkey, json_encoded_request_body, 'sha512')
            base64_encoded_request_body = base64.b64encode(signed_request_body)
            r = requests.post(f'{self.api}/auth',
                              data=json_encoded_request_body,
                              headers={'Signature': base64_encoded_request_body})

            if r.status_code != 201:
                raise TransIPException(r.status_code, json.loads(r.text)['error'])

            logging.debug(f'Created new auth token with label {request_body["label"]}')
            return json.loads(r.text)['token']

    @property
    def _headers(self) -> Dict:
        if self._authorization is None:
            self._authorization = self._get_authorization()
        return {'Authorization': f'Bearer {self._authorization}'}

    def _request(self,
                 method: Callable,
                 url: AnyStr,
                 data: Optional[AnyStr] = None,
                 retry: bool = True) -> requests.Response:

        r = method(f'{self.api}{url}', data=data, headers=self._headers)

        if r.status_code == 401:
            if retry:
                self._authorization = None
                return self._request(method, url, data, False)

        return r

    def _get_entries(self) -> List[Dict]:
        r = self._request(requests.get, f'/domains/{self.domain}/dns')

        if r.status_code != 200:
            if r.status_code == 404:
                raise TransIPException(r.status_code, json.loads(r.text)['error'])
            elif r.status_code == 406:
                raise TransIPException(r.status_code, json.loads(r.text)['error'])
            else:
                raise Exception('Unexpected status code')

        return json.loads(r.text)['dnsEntries']

    def _add_entry(self, entry: Dict) -> None:
        r = self._request(requests.post, f'/domains/{self.domain}/dns', json.dumps({
            'dnsEntry': entry
        }))

        if r.status_code != 201:
            if r.status_code == 403:
                raise TransIPException(r.status_code, json.loads(r.text)['error'])
            elif r.status_code == 404:
                raise TransIPException(r.status_code, json.loads(r.text)['error'])
            elif r.status_code == 406:
                raise TransIPException(r.status_code, json.loads(r.text)['error'])
            elif r.status_code == 409:
                raise TransIPException(r.status_code, json.loads(r.text)['error'])
            else:
                raise Exception('Unexpected status code')

        logging.info(f'Added DNS entry {entry}')

    def _update_entry(self, entry: Dict) -> None:
        r = self._request(requests.patch, f'/domains/{self.domain}/dns', json.dumps({
            'dnsEntry': entry
        }))

        if r.status_code != 204:
            if r.status_code == 403:
                raise TransIPException(r.status_code, json.loads(r.text)['error'])
            elif r.status_code == 404:
                raise TransIPException(r.status_code, json.loads(r.text)['error'])
            elif r.status_code == 406:
                raise TransIPException(r.status_code, json.loads(r.text)['error'])
            elif r.status_code == 409:
                raise TransIPException(r.status_code, json.loads(r.text)['error'])
            else:
                raise Exception('Unexpected status code')

        logging.info(f'Updated DNS entry {entry}')

    def update(self, ip_address: AnyStr, dns: List[Dict]) -> None:
        old_entries = self._get_entries()

        for entry in dns:
            new_entry = dict(entry, content=entry['content'] % {'ip': '.'.join([str(i) for i in ip_address])})
            if new_entry in old_entries:
                logging.info(f'Skipped already existing entry {new_entry}')
                continue

            if not len([old_entry for old_entry in old_entries if self.compare_dns(new_entry, old_entry)]):
                self._add_entry(new_entry)
            else:
                self._update_entry(new_entry)
