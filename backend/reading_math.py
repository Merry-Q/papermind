"""Render model-authored mathematical text to native MathML at build time."""
from html.parser import HTMLParser
from functools import lru_cache
import json,re,subprocess
from . import store

class MathText(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=False);self.parts=[];self.math=[];self.stack=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs);self.parts.append(self.get_starttag_text());self.stack.append((tag,'formula' in attrs.get('class','')))
        if tag in {'input','br','hr'}:self.stack.pop()
    def handle_startendtag(self,tag,attrs):self.parts.append(self.get_starttag_text())
    def handle_endtag(self,tag):
        self.parts.append('</'+tag+'>')
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i][0]==tag:self.stack=self.stack[:i];break
    def add(self,tex):
        i=len(self.math);self.math.append(tex.strip());return f'@@PMMATH{i}@@'
    def handle_data(self,text):
        if any(flag for _,flag in self.stack) and '\\' in text and '$' not in text:
            self.parts.append(self.add(text))
        else:self.parts.append(re.sub(r'\$\$([^$]+)\$\$|\$([^$\n]+)\$',lambda m:self.add(m.group(1) or m.group(2)),text))
    def handle_entityref(self,name):self.parts.append('&'+name+';')
    def handle_charref(self,name):self.parts.append('&#'+name+';')
    def handle_comment(self,data):self.parts.append('<!--'+data+'-->')

@lru_cache(maxsize=32)
def render_math(markup):
    parser=MathText();parser.feed(markup)
    if not parser.math:return markup
    result=subprocess.run(['node',str(store.ROOT/'scripts/render-reading-math.mjs')],input=json.dumps(parser.math),capture_output=True,text=True,encoding='utf-8',timeout=30,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if result.returncode:raise ValueError('数学排版失败：'+result.stderr[:300])
    values=json.loads(result.stdout);output=''.join(parser.parts)
    for i,value in enumerate(values):output=output.replace(f'@@PMMATH{i}@@',value)
    return output
