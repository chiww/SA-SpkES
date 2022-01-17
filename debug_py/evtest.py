# coding=utf-8

#
# Windag search operator
#
# Generates structured data for development use.
#
# Usage:
#
#   At the most basic level, you can just do 'windbag'.  The arguments
#   listed below in DEFAULT_ARGS can all be overridden as search arguments in
#   the search string, i.e., 'windbag multiline=true rowcount=3000'.  From the
#   current UI, prefix the search string with a pipe, i.e. '| windbag'
#

import os, sys, time, datetime
import splunk.util as util
import splunk.Intersplunk as isp
import logging as logger
from builtins import range
import csv
if sys.version_info >= (3, 0):
    from io import (BytesIO, TextIOWrapper)
else:
    from StringIO import StringIO
    BytesIO = StringIO
from future.moves.urllib import parse as urllib_parse

DEFAULT_ARGS = {

    'rowcount': 100,
    'multiline': False,
    'distribution': 'flat',

    'timeformat': 1,
    'interval': 60 * 17,
    'basetime': time.time(),
    'timeorder': 'reverse',

    'fieldcount': 0,
    'constant': '"double quotes" \'single quotes\' \\slashes\\ `~!@#$%^&*()-_=+{}|;:<>,./? [brackets]',
    'host': 'HAL_9000',
    'source': 'SpaceOdyssey',
    'sourcetype': 'fictional',
    'punct': '`~!@#$%^&*()-_=+\\"\'{}|;:<>,./?[]',

    'filler': '',
    'utf8': True,
    'mvfield': ''
}

ARG_SEPARATOR = ';'

utf8Samples = [
    ('Albanian', 'Unë mund të ha qelq dhe nuk më gjen gjë.'),
    ('Arabic', 'أنا قادر على أكل الزجاج و هذا لا يؤلمني.', 'ltr'),
    ('Armenian', 'Կրնամ ապակի ուտել և ինծի անհանգիստ չըներ։'),
    ('Chinese', ' 我能吞下玻璃而不傷身體'),
    ('Danish', 'Jeg kan spise glas, det gør ikke ondt på mig.'),
    ('Euro', '€.'),
    ('French', 'Je peux manger du verre, ça ne me fait pas de mal.'),
    ('Georgian', 'მინას ვჭამ და არა მტკივა.'),
    ('Greek', 'Μπορώ να φάω σπασμένα γυαλιά χωρίς να πάθω τίποτα.'),
    ('Hawaiian', 'Hiki iaʻu ke ʻai i ke aniani; ʻaʻole nō lā au e ʻeha.'),
    ('Hebrew', 'אני יכול לאכול זכוכית וזה לא מזיק לי.', 'ltr'),
    ('Hindi', 'मैं काँच खा सकता हूँ और मुझे उससे कोई चोट नहीं पहुंचती.'),
    ('Hindi', 'मैं काँच खा सकता हूँ, मुझे उस से कोई पीडा नहीं होती.'),
    ('Icelandic', 'Ég  get etið gler án þess að meiða mig.'),
    ('Japanese', '私はガラスを食べられます。それは私を傷つけません'),
    ('Korean', '나는 유리를 먹을 수 있어요. 그래도 아프지 않아요'),
    ('Macedonian', 'Можам да јадам стакло, а не ме штета.'),
    ('Mongolian', 'Би шил идэй чадна, надад хортой биш'),
    ('Old Norse', 'Ek get etið gler án þess að verða sár.'),
    ('Polish', 'Mogę jeść szkło, i mi nie szkodzi.'),
    ('Romanian', 'Pot să mănânc sticlă și ea nu mă rănește.'),
    ('Serbian', 'Mogu jesti staklo a da mi ne škodi.'),
    ('Tamil', 'நான் கண்ணாடி சாப்பிடுவேன், அதனால் எனக்கு ஒரு கேடும் வராது.'),
    ('Thai', 'ฉันกินกระจกได้ แต่มันไม่ทำให้ฉันเจ็บ'),
    ('Ukrainian', 'Я можу їсти шкло, й воно мені не пошкодить.'),
    ('Ukrainian', 'Я можу їсти шкло, й воно мені не пошкодить.'),
    ('Vietnamese', 'Tôi có thể ăn thủy tinh mà không hại gì.'),
    ('Yiddish', 'איך קען עסן גלאָז און עס טוט מיר נישט װײ.', 'ltr')
]




#
# main
#

# merge any passed args
args = DEFAULT_ARGS
for item in sys.argv:
    kv = item.split('=')
    if len(kv) > 1:
        val = item[item.find('=') + 1:]
        try:
            val = int(val)
        except:
            pass
        args[kv[0]] = util.normalizeBoolean(val)

# run generator
basetime = float(args['basetime'])

hosts = args['host'].split(ARG_SEPARATOR)
sources = args['source'].split(ARG_SEPARATOR)
sourcetypes = args['sourcetype'].split(ARG_SEPARATOR)

# =========================================


# =========================================
o = list()
for i in range(args['rowcount']):

    rowset = {}
    # set time
    timedir = -1
    if args['timeorder'] == 'forward': timedir = 1
    timestamp = basetime + (args['interval'] * i) * timedir
    raw = [datetime.datetime.fromtimestamp(timestamp).isoformat()]
    rowset['_time'] = timestamp

    # set row number
    raw.append('POSITION %d' % i)
    rowset['position'] = i

    # set primary stuff
    rowset['host'] = hosts[i % len(hosts)]
    rowset['source'] = sources[i % len(sources)]
    rowset['sourcetype'] = sourcetypes[i % len(sourcetypes)]
    # rowset['_cd'] = 234

    # insert unicode samples
    if args['utf8']:
        # if args['multiline']:
        #     sample = []
        #     for j in range(i, i + 5):
        #         sample.append(utf8Samples[j % (len(utf8Samples) - 1)][1])
        #     raw.append('\n'.join(sample))
        # else:
        sample = utf8Samples[i % (len(utf8Samples) - 1)]
        raw.append('lang=%s sample="%s"' % (sample[0], sample[1]))
        rowset['lang'] = sample[0]
        rowset['sample'] = sample[1]

        # add high-bit field name
        sample = utf8Samples[i % (len(utf8Samples) - 1)]
        rowset[sample[1].split(' ')[0]] = 'field value in %s' % sample[0]

    # # set filler
    # if args['filler']:
    #     raw.append(args['filler'])
    #
    # # gen odd fields
    # if i % 2 != 0:
    #     rowset['odd'] = i
    #     raw.append('odd=%s' % i)
    #
    # # gen constant field value
    # rowset['fancy_constant_field'] = args['constant']
    # raw.append('constant=%s' % args['constant'])

    # gen script injection test
    # rowset['<script>alert("field_name_unescaped!")</script>'] = 'field_name_exploit_test'
    # rowset['field_value_exploit_test'] = '<script>alert("field_value_unescaped!")</script>'
    # raw.append('<script>alert("raw event unescaped!")</script>')

    # set fields
    # for j in range(args['fieldcount']):
    #     fieldName = 'field%s' % j
    #     value = (i + 2) * (j + 2)
    #     rowset[fieldName] = value
    #     raw.append('%s=%s' % (fieldName, value))

    # construct the raw item
    splitter = ' '
    rowset['_raw'] = splitter.join(raw)

    # set punct
    # rowset['punct'] = args['punct']

    # add a multivalued field?
    # if args['mvfield']:
    #     if (i % 3 == 0):
    #         rowset[args['mvfield']] = [str(i)]
    #     elif (i % 3 == 1):
    #         rowset[args['mvfield']] = [str(i), str(i * i)]
    #     else:
    #         rowset[args['mvfield']] = [str(i), str(i * i), str(i * i * i)]

            # add to result set
    # ------------
    o.append(rowset)
# isp.outputStreamResults(o)
    new_row_set = dict()
    h = []
    for key, value in rowset.items():
        # if isinstance(value, list):
        #     new_row_set['__mv_' + key] = isp.getEncodedMV(value)
        #     value = '\n'.join(value)
        # else:
        #     new_row_set[key] = value

        new_row_set[key] = value

        h.append(key)

    # ======
    outputfile = isp.default_stdout_stream()
    if sys.version_info >= (3, 0):
        outputfile = TextIOWrapper(outputfile, encoding='utf-8', write_through=True)


    dw = csv.DictWriter(outputfile, h, extrasaction='ignore')
    dw.writerow(dict(zip(h, h)))
    dw.writerow(new_row_set)
    if sys.version_info >= (3, 0):
        outputfile.detach()  # Don't close the underlying file



