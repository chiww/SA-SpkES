#!/usr/bin/env python
import sys
sys.path.insert(0, '/opt/splunk/lib/python3.7/site-packages')
import splunk.Intersplunk as spi
import requests, time


class SearchSDK(object):

    def __init__(self, query, timeout):
        self.__base_url = "https://127.0.0.1:8089"
        self.__auth_key = {'Authorization': "Basic YWRtaW46d2Vpd2VpQDIwMjA="}
        self.__query = str(query)
        self.__timeout = int(timeout)
        self.spi = spi

    def create_search(self):
        try:
            body = {"search": self.__query, "output_mode": "json"}
            response = requests.request("POST", "{0}/services/search/jobs".format(self.__base_url), data=body,
                                        headers=self.__auth_key,
                                        verify=False).json()
            if "sid" in response.keys():
                return str(response["sid"])

        except Exception as e:
            spi.parseError("[+] ERROR Create Search, Reason: {}".format(e))

    def invoke_status(self):
        try:
            sid = self.create_search()
            timer = 0
            while timer < self.__timeout:
                timer += 1
                time.sleep(1)

                response = requests.get(
                    "{0}/services/search/jobs/{1}/?output_mode=json".format(self.__base_url, sid),
                    verify=False, headers=self.__auth_key).json()

                if response["entry"][0]["content"]["dispatchState"] == "DONE":
                    break
            return sid

        except Exception as e:
            spi.parseError("[+] ERROR Invoke Status, Reason: {}".format(e))

    def invoke_results(self):
        try:
            response = requests.get(
                "{0}/services/search/jobs/{1}/results/?output_mode=json".format(self.__base_url,
                                                                                self.invoke_status()),
                verify=False, headers=self.__auth_key).json()
            results = response["results"]
            # spi.parseError("[+] {}".format(json.dumps(response["results"])))
            return results

        except Exception as e:
            spi.parseError("[+] ERROR Invoke Status, Reason: {}".format(e))

    def printf(self, *args):
        spi.parseError(args)


if __name__ == '__main__':

    # example
    # query = "search index=_internal earliest=-15m@m | table index source"
    query = "search index=_internal earliest=-15m@m"
    sdk = SearchSDK(query, 1000)
    print(sdk.invoke_results())