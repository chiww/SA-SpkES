#!/usr/bin/env python
import os
os.environ.setdefault('SPLUNK_HOME', '/opt/splunk')
os.environ.setdefault('SPLUNK_DB', '/opt/splunk/var/lib/splunk')

# LD_LIBRARY_PATH=/opt/splunk/lib:/opt/splunk/bin/jars/vendors/java/OpenJDK8U-jre_x64_linux_hotspot_8u242b08/lib/amd64:/opt/splunk/bin/jars/vendors/java/OpenJDK8U-jre_x64_linux_hotspot_8u242b08/lib/amd64/jli
# OPENSSL_CONF=/opt/splunk/openssl/openssl.cnf
# SSL_CERT_FILE=/opt/splunk/openssl/cert.pem
# LDAPCONF=/opt/splunk/etc/openldap/ldap.conf
os.environ.setdefault('LD_LIBRARY_PATH', '/opt/splunk/lib:/opt/splunk/bin/jars/vendors/java/OpenJDK8U-jre_x64_linux_hotspot_8u242b08/lib/amd64:/opt/splunk/bin/jars/vendors/java/OpenJDK8U-jre_x64_linux_hotspot_8u242b08/lib/amd64/jli')
os.environ.setdefault('OPENSSL_CONF', '/opt/splunk/openssl/openssl.cnf')
os.environ.setdefault('SSL_CERT_FILE', '/opt/splunk/openssl/cert.pem')
from splunk.auth import getSessionKey
from splunk.search import dispatch

key = getSessionKey('admin', 'weiwei@2020')

# start the search
job = dispatch('search index=*', sessionKey=key)

# iterate over the raw events; stop at 10
for idx, event in enumerate(job.events):
    print(event)
    if idx > 10:
        break

# do direct selection of events 2 to 3:
print(job.events[2:3])

# check the job status
if job.isDone:
    print("The search job=%s is finished" % job.id)

# get the raw XML output for first 5 events
print(job.getFeed(mode='events', count=5))

# clean up
job.cancel()