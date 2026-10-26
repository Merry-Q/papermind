"""Document-scoped lexical retrieval and real Qwen web search with source fetching."""
import hashlib
import ipaddress
import math
import re
import socket
import time
import xml.etree.ElementTree as ET
from collections import Counter
from html.parser import HTMLParser
from urllib.parse import urljoin,urlparse
import httpx
import pymupdf
from . import model_gateway as gateway, settings

def tokens(text):
    result = re.findall(r'[a-zA-Z][a-zA-Z0-9_-]{1,}|[\u4e00-\u9fff]',text.lower())
    chinese = re.findall(r'[\u4e00-\u9fff]+',text)
    return result + [part[i:i+2] for part in chinese for i in range(len(part)-1)]

def retrieve(sources, query, limit=16, preferred=None):
    q = Counter(tokens(query))
    docs = [Counter(tokens(s.get('quote',''))) for s in sources]
    df = Counter(t for d in docs for t in d)
    average = sum(sum(d.values()) for d in docs)/max(1,len(docs))
    scores=[]
    for source,counts in zip(sources,docs):
        length=sum(counts.values())
        score=sum(math.log(1+(len(docs)-df[t]+.5)/(df[t]+.5))*counts[t]*2.2/(counts[t]+1.2*(.25+.75*length/max(1,average))) for t in q if counts[t])
        if preferred and source['id'] in preferred:
            score+=8
        scores.append((score,source))
    return [s for _,s in sorted(scores,key=lambda x:x[0],reverse=True)[:limit]]

class TextReader(HTMLParser):
    def __init__(self):
        super().__init__();self.parts=[];self.skip=0;self.title=[];self.in_title=False
    def handle_starttag(self,tag,attrs):
        if tag in {'script','style','noscript','nav','footer'}:self.skip+=1
        if tag=='title':self.in_title=True
    def handle_endtag(self,tag):
        if tag in {'script','style','noscript','nav','footer'}:self.skip=max(0,self.skip-1)
        if tag=='title':self.in_title=False
    def handle_data(self,data):
        if self.in_title:self.title.append(data.strip())
        if not self.skip and data.strip():self.parts.append(data.strip())

def public_url(url):
    parsed=urlparse(url)
    if parsed.scheme not in {'http','https'} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('来源 URL 协议或身份信息不允许')
    if parsed.port not in {None,80,443}:
        raise ValueError('不允许访问非标准端口')
    addresses=socket.getaddrinfo(parsed.hostname,parsed.port or (443 if parsed.scheme=='https' else 80))
    if any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError('不能从外部检索访问本机或私有网络')
    return url

def fetch_source(url):
    for _ in range(4):
        public_url(url)
        with httpx.Client(timeout=25,trust_env=False,follow_redirects=False,headers={'User-Agent':'paperMind/0.2 research reader'}) as c:
            with c.stream('GET',url) as response:
                if response.is_redirect:
                    url=urljoin(url,response.headers['location']);continue
                response.raise_for_status()
                chunks=[];length=0
                for part in response.iter_bytes():
                    length+=len(part)
                    if length>12*1024*1024:raise ValueError('外部来源超过12MB读取上限')
                    chunks.append(part)
                raw=b''.join(chunks)
        if raw.startswith(b'%PDF-'):
            with pymupdf.open(stream=raw,filetype='pdf') as pdf:
                # Preserve paragraphs across PDF line wraps. Filtering raw lines
                # by length used to retain captions but drop academic prose.
                text='\n'.join(' '.join(str(b[4]).split()) for p in pdf[:min(12,len(pdf))] for b in p.get_text('blocks') if len(b)>6 and b[6]==0)
                title=pdf.metadata.get('title') or urlparse(url).path.split('/')[-1]
                scope=f'PDF前{min(12,len(pdf))}页，未读取其余页'
        else:
            reader=TextReader();reader.feed(raw.decode('utf-8',errors='replace'))
            text='\n'.join(reader.parts);title=' '.join(reader.title) or urlparse(url).hostname
            scope='网页正文抽取'
        if len(text.strip())<180:raise ValueError('来源没有足够可读正文，可能受访问限制')
        return {'url':url,'title':title,'text':text[:60000],'scope':scope,'content_hash':hashlib.sha256(raw).hexdigest()}
    raise ValueError('来源重定向过多')

def find_search_results(data):
    if isinstance(data,dict):
        for key,value in data.items():
            if key=='search_results' and isinstance(value,list):return value
            found=find_search_results(value)
            if found:return found
    if isinstance(data,list):
        for value in data:
            found=find_search_results(value)
            if found:return found
    return []

def scholarly_source(url):
    host=(urlparse(url).hostname or '').lower()
    trusted=('arxiv.org','doi.org','nber.org','imf.org','worldbank.org','cnnic.cn','acm.org','ieee.org','nature.com','science.org','sciencedirect.com','springer.com','springeropen.com','wiley.com','oup.com','cambridge.org','mdpi.com','plos.org','frontiersin.org','apa.org','jstor.org','royalsocietypublishing.org','ncbi.nlm.nih.gov')
    return any(host==t or host.endswith('.'+t) for t in trusted) or host.endswith(('.edu','.edu.cn','.ac.uk','.ac.jp','.gov','.gov.cn','.int'))

def academic_index(query):
    """Independent public bibliography fallback; returns observed URLs, never invented citations."""
    phrase=re.split(r'\bdefinition\b|\btextbook\b|\bderivation\b|\bOR\b',query,flags=re.I)[0].strip(' \"')
    stop={'explain','the','mathematical','definition','and','role','of','in','use','original','paper','as','evidence','understanding','what','is','why','how'}
    words=[w for w in re.findall(r'[a-zA-Z][a-zA-Z0-9-]+',phrase) if w.lower() not in stop]
    if len(words)<2:return []
    expression='all:"'+' '.join(words)+'"' if len(words)==2 else ' AND '.join('all:'+w for w in words[:3])
    with httpx.Client(timeout=20,trust_env=False,follow_redirects=True) as client:
        response=client.get('https://export.arxiv.org/api/query',params={'search_query':expression,'start':0,'max_results':6,'sortBy':'relevance','sortOrder':'descending'})
    response.raise_for_status()
    tree=ET.fromstring(response.text);ns={'a':'http://www.w3.org/2005/Atom'}
    result=[]
    for entry in tree.findall('a:entry',ns):
        link=entry.find('a:id',ns);title=entry.find('a:title',ns)
        if link is not None and link.text and '/abs/' in link.text:
            url=link.text.replace('http://','https://').replace('/abs/','/pdf/')
            result.append({'title':title.text if title is not None else '', 'url':url,'discovery':'arxiv_atom_api'})
    return result

def web_search(query, *, context=None, max_sources=3):
    if not settings.live_enabled():raise gateway.ModelError('联网取证需要阿里云模型凭证')
    started=time.monotonic(); model=settings.models()['search']
    payload={'model':model,'input':{'messages':[{'role':'user','content':'请联网查找能支持以下专业问题的原始文献、教材、大学或官方来源。优先 arxiv.org、plato.stanford.edu、mit.edu、nber.org 和学术出版机构。不要使用个人博客、知乎、CSDN作为专业定义的依据。不要仅凭记忆作答。问题：'+query}]},
             'parameters':{'enable_search':True,'search_options':{'forced_search':True,'enable_source':True,'enable_citation':True},'result_format':'message','max_tokens':1200,'enable_thinking':False}}
    with gateway.LIMIT:
        with httpx.Client(timeout=120,trust_env=False) as client:
            response=client.post(settings.NATIVE+'/services/aigc/text-generation/generation',headers={'Authorization':'Bearer '+settings.api_key()},json=payload)
    if not response.is_success:
        gateway.audit('search',model,round(time.monotonic()-started,3),{},'failed',context)
        raise gateway.ModelError('阿里云联网检索失败：'+str(response.status_code)+' '+settings.sanitize(response.text))
    data=response.json();results=find_search_results(data)
    gateway.audit('search',model,round(time.monotonic()-started,3),data.get('usage',{}),'ok' if results else 'no_sources',context)
    if not any(scholarly_source(item.get('url','')) for item in results):
        payload['input']['messages'][0]['content']='检索权威学术来源，返回实际来源。site:arxiv.org OR site:edu OR site:ac.uk '+query
        with gateway.LIMIT:
            with httpx.Client(timeout=120,trust_env=False) as client:
                second=client.post(settings.NATIVE+'/services/aigc/text-generation/generation',headers={'Authorization':'Bearer '+settings.api_key()},json=payload)
        if second.is_success:
            second_data=second.json();results+=find_search_results(second_data)
            gateway.audit('search',model,round(time.monotonic()-started,3),second_data.get('usage',{}),'academic_retry',context)
    errors=[];sources=[]
    try:results=academic_index(query)+results
    except Exception as error:errors.append({'url':'https://export.arxiv.org/api/query','error':'公开学术索引查询未完成：'+settings.sanitize(error)})
    # A model-provided URL isn't evidence until its content has actually been read.
    for item in results:
        url=item.get('url')
        if not url or any(s['url']==url for s in sources):continue
        parsed=urlparse(url)
        if parsed.path.rstrip('/') in {'','/search','/help','/about','/archive'}:
            errors.append({'url':url,'error':'网站首页/目录不作为专业定义证据'})
            continue
        if not scholarly_source(url):
            errors.append({'url':url,'error':'来源未通过学术/机构域名筛选，不用于关键专业知识依据'})
            continue
        if url.startswith('http://doi.org/'):url='https://doi.org/'+url.split('doi.org/',1)[1]
        if (urlparse(url).hostname or '')=='arxiv.org' and '/abs/' in url:
            url=url.replace('/abs/','/pdf/')
        try:
            fetched=fetch_source(url)
            query_words={w for w in re.findall(r'[a-zA-Z][a-zA-Z0-9-]{2,}',query.lower()) if w not in {'definition','textbook','source','explain','original','paper','the','and','for','with','from'}}
            if len(query_words)>=2 and len(query_words & set(re.findall(r'[a-zA-Z][a-zA-Z0-9-]{2,}',fetched['text'].lower())))<min(2,len(query_words)):
                raise ValueError('正文与检索概念相关性不足，不能作为定义依据')
            passages=[p for p in fetched['text'].split('\n') if len(p.strip())>5]
            ranked=retrieve([{'id':str(i),'quote':p} for i,p in enumerate(passages)],query,limit=5)
            # Keep definitions/equations next to matching paragraphs, including
            # short formula blocks. Isolated captions are not enough evidence.
            indices={j for p in ranked for j in range(max(0,int(p['id'])-2),min(len(passages),int(p['id'])+3))}
            quote='\n'.join(passages[j] for j in sorted(indices))[:12000] or fetched['text'][:12000]
            title=fetched['title'] if len(fetched['title'].strip('% '))>3 else item.get('title') or fetched['url']
            sources.append({'id':'web-'+hashlib.sha256(fetched['url'].encode()).hexdigest()[:16], 'kind':'external','title':title,'page':0,'quote':quote,'locator':fetched['scope'],'status':'retrieved','url':fetched['url'],'content_hash':fetched['content_hash'],'source_filter':'academic_or_institutional'})
            if len(sources)>=max_sources:break
        except Exception as error:errors.append({'url':url,'error':settings.sanitize(error)})
    return {'query':query,'sources':sources,'search_result_count':len(results),'fetch_errors':errors}
