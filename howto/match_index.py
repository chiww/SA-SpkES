

# 只支持通配符*
configure = {
    'index:*': {
        'timefield': '@timestamp',
        'timeformat': '%Y-%m-%dT%H:%M:%S.%fZ'
    },
    'index:bank': {
        'timefield': '@timestamp',
        'timeformat': '%Y-%m-%dT%H:%M:%S.%fZ'
    },
    'index:logstash-*': {
        'timefield': '@timestamp',
        'timeformat': '%Y-%m-%dT%H:%M:%S.%fZ'
    },
}

# https://segmentfault.com/a/1190000023095987
# class Solution:
#     def isMatch(self, pre: str, cur: str) -> bool:
#         i, j, prestar, match = 0, 0, -1, -1
#         while i < len(pre):
#             if j < len(cur) and (pre[i] == cur[j] or cur[j] == "?" ):
#                 i += 1
#                 j += 1
#             elif j < len(cur) and cur[j] == "*":
#                 prestar = j
#                 j += 1
#                 match = i
#             elif prestar != -1:
#                 j = prestar + 1
#                 i = match + 1
#                 match = i
#             else:
#                 return False
#         # 上一段代码只跟踪了字符串s，也就是pre，如果字符模式p字符串后面还有字符，如果后面的字符是*，那么可以继续看下一个字符
#         while j < len(cur) and cur[j] == "*":
#             j += 1
#         # 如果当前位置不为字符串p的长度，说明做字符串p的*后面（如果有），还有未匹配的字符，说明两个字符串不完全匹配
#         return j == len(cur)


def is_match(pre: str, cur: str) -> bool:
    i, j, prestar, match = 0, 0, -1, -1
    while i < len(pre):
        if j < len(cur) and (pre[i] == cur[j] or cur[j] == "?"):
            i += 1
            j += 1
        elif j < len(cur) and cur[j] == "*":
            prestar = j
            j += 1
            match = i
        elif prestar != -1:
            j = prestar + 1
            i = match + 1
            match = i
        else:
            return False
    # 上一段代码只跟踪了字符串s，也就是pre，如果字符模式p字符串后面还有字符，如果后面的字符是*，那么可以继续看下一个字符
    while j < len(cur) and cur[j] == "*":
        j += 1
    # 如果当前位置不为字符串p的长度，说明做字符串p的*后面（如果有），还有未匹配的字符，说明两个字符串不完全匹配
    return j == len(cur)


print(is_match('logstash-*', 'logstash-2015*'))




