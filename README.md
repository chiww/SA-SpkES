# SA-SpkES Splunk搜索Elasticsearch

**该项目是开发环境，可以在release中下载可以直接使用的安装包**

**该开发框架是基于splunklib中的samplecommand-apps修改而来，该开发如何使用，可以参考相关文档**

## 简介

Splunk和基于Elasticsearch的ELK技术栈都是日志分析领域两个使用频率较高的产品。Splunk作为一款昂贵的商业产品，其用户体验要优于Elasticsearch，用过的Splunk的人都会”真香“。

实际环境中，可能会存在以下几个问题：

1. 因Splunk订阅费昂贵，未必所有日志都往Splunk存，不能存的日志第一选择是存在Elasticsearch；
2. 如果已经存在Elasticsearch中的数据要在Splunk中检索，要么使用转发工具将日志迁移到Splunk，要么重新从数据源接一份数据到Splunk，这种做法成本相当费时费力；
3. 各种日志离散存储在不同Elasticsearch中，不同类型数据库很难快速关联查找；

其实基于Splunk开放的能力，是可以通过`自定义搜索命令`来打通各存储类型之间的链接。这点在Splunk官方文档中对`自定义搜索命令场景`描述中，就提到了”将非Splunk的外部数据导入到Splunk搜索通道中“的能力。

Splunk搜索命令是基于通道的，能够将Elasticsearch的数据嵌入到Splunk的搜索通道中，这样可以有两个好处：

1. 可以在Splunk直接对Elasticsearch检索，相当于在Splunk中构建一个Elasticsearch客户端。这里可能有人要问了，Kibana已经Elasticsearch客户端了，为什么还要多此一举使用Splunk来做统一检索呢？笔者觉得Splunk检索语法支持通道，检索语句可以更灵活，其使用场景更丰富。
2. 搜索通道中的数据是可以相互关联，做lookup操作的，意味着不同的日志之间可以互相富化，提高日志使用质量。 
3. 通过自定义命令获取的数据是不会在Splunk中落地的，意味着不会占用Splunk的订阅License，相当于一定程度的“白嫖”。

总的来说，对于Splunk重度用户，可以将部分数据保留在Elasticsearch集群上，在不影响使用体验的前提下可以有效降低License费用；对于混用Splunk和Elasticsearch用户，可以将搜索体验统一化，提供更好的用户体验；对于想白嫖的用户，也完全可以申请一个开发者License（每天10G，免费），在数据不落地的场景下使用Splunk的功能。

## 安装使用

本项目是个人开发环境，包含在写这个项目各种记录和临时文件，App主要代码在`SA-SpkES`目录下；

### 生成App
如果需要修改代码重新生成App安装包，可以按照以下方式生成
```
> git clone https://github.com/chiww/SA-SpkES.git
> cd SA-SpkES/SA-SpkES
> ./Build-App
```
新生成的App会在`SA-SpkES/build`目录下，使用以下命令安装到Splunk中:
```
/opt/splunk/bin/splunk install app SA-SpkES-1.0.0-<版本号>.tar.gz -update 1
```

### 基本使用

SA-SpkES核心有两个命令：

 - essearch
 - eslookup 

这两个命令使用在不同场景中。

**essearch**

`essearch`是直接检索Elasticsearch用的，可以简单理解就是`Elasticsearch在Splunk实现的检索客户端`，这个命令必须放在检索语句最前面，是用于`产生数据`的；执行该命令后，从Elasticsearch检索到的数据就会进入到Splunk工作流中。
例如，在Splunk直接检索Elasticsearch，SPL可以使用自定义命令`essearch`这样写:

```
| essearch index="logstash-2015*" query=*
```
`index` 和`query`分别对应着Elasticsearch中的Index和`query_string`的检索语句。

![essearch](C:\<MUST_BE_REPLACE_AFTER_FIRST_COMMIT>\essearch.png)

**eslookup**

`eslookup`是用于检索语句中存在上下文关联的检索，例如这样的SPL语句：

```
| makeresults 
| eval q="POINS" 
| eslookup index=shakesp* query="speaker:{q}"
```

`eslookup`是自定义命令，这个SPL语句中除最后一行外，其余前面几行可以看成是`eslookup`的上文信息。例如该实例中，`q`这个字段的值是前一个搜素语句的结果，该结果可以作为`eslookup`这个命令`query`参数的补充，填充到Elasticsearch`query_string`的检索语句中。

![eslookup01](C:\<MUST_BE_REPLACE_AFTER_FIRST_COMMIT>\eslookup01.PNG)

也可以是填充多个值，例如如下这样的SPL:

```
| makeresults 
| eval q="POINS" 
| append 
    [ makeresults 
    | eval q="FALSTAFF" ] 
| stats values(q) as q 
| eslookup index=shakesp* query="speaker:{q}"
```

![eslookup02](C:\<MUST_BE_REPLACE_AFTER_FIRST_COMMIT>\eslookup02.PNG)


## 关于
有关该App更详细说明，可以参考公众号`安小记`文章[在Splunk中检索Elasticsearch数据]()
