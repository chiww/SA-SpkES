import re
import traceback


def is_query_format(q):

    return re.match(r'.*(\{.*?}).*', q)


query = [
    '{fieldA} is {fieldB} and some other message.',
    'some not have format.',
    'fieldA: {fieldA} AND fieldB:{fieldB}'
]


def func_a():

    # want result is:
    #   "valueA is valueB and some other message."

    records = [
        {'fieldA': 'valueA1', 'fieldB': 'valueB1', 'fieldC': 'valueC1'},
        {'fieldA': 'valueA2', 'fieldB': 'valueB2'},
        {'fieldA': 'valueA3', 'fieldB': 'valueB3'}
    ]

    def parser(q):
        for record in records:
            try:
                if is_query_format(q):
                    print(q.format(**record))
            except KeyError as e:
                print(e)
                print(traceback.format_exc())
                continue

    for q in query:
        print(">>>>>>  " + q)
        print(parser(q))


def func_b():

    # want result is:
    #   "fieldA:(valueA1 OR valueB1 OR valueC1) AND fieldB: valueB2"

    records = [
        {'fieldA': 'valueA1', 'fieldB': 'valueB1', 'fieldC': 'valueC1'},
        {'fieldA': ['valueAA1', 'valueAA2', 'valueAA3'], 'fieldB': 'valueB2'},
        {'fieldA': 'valueA3', 'fieldB': 'valueB3'}
    ]

    fieldnames = ['fieldA', 'fieldB', 'fieldC', 'fieldD']

    def parser(q):
        for record in records:
            handler_keys = list(set(record.keys()).intersection(set(fieldnames)))
            print(handler_keys)

            for key in handler_keys:
                if isinstance(record[key], list):
                    record[key] = "(%s)" % " OR ".join(record[key])

            print(q.format(**record))

    for q in query:
        print(">>>>>>  " + q)
        print(parser(q))


if __name__ == '__main__':
    func_b()













