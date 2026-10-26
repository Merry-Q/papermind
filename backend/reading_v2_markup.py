"""Deterministic assembly of attributed chapter sections and local identifiers."""
from html import escape
from html.parser import HTMLParser
import re

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}


class Sections(HTMLParser):
    def __init__(self, markup):
        super().__init__(convert_charrefs=False)
        self.markup = markup
        self.offsets = [0]
        for match in re.finditer('\n', markup): self.offsets.append(match.end())
        self.stack = []
        self.elements = []
        self.ids = set()

    def pos(self):
        line, col = self.getpos()
        return self.offsets[line - 1] + col

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'): self.ids.add(attrs['id'])
        if tag not in VOID:
            self.stack.append({'tag': tag, 'attrs': attrs, 'start': self.pos(),
                               'content': self.pos() + len(self.get_starttag_text())})

    def handle_startendtag(self, tag, attrs):
        if dict(attrs).get('id'): self.ids.add(dict(attrs)['id'])

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]['tag'] == tag:
                element = self.stack[i]
                element['end'] = self.pos() + len(tag) + 3
                self.elements.append(element)
                del self.stack[i:]
                return


def normalize(artifact, node_ids, chapter_id, *, namespace=True):
    """Keep existing author selectors intact; give actual attributed content its anchor."""
    value = dict(artifact)
    scan = Sections(value['html']); scan.feed(value['html'])
    inserts = []
    for node_id in set(node_ids) - scan.ids:
        matches = [e for e in scan.elements if e['attrs'].get('data-node') == node_id
                   and e['tag'] in {'section', 'article', 'div', 'main'}
                   and 'hidden' not in e['attrs']
                   and not re.search(r'display\s*:\s*none|visibility\s*:\s*hidden', e['attrs'].get('style', ''))
                   and len(re.sub('<[^>]+>', '', value['html'][e['content']:e['end']]).strip()) > 40]
        if len(matches) != 1:
            continue  # Ambiguous/unattributed content must still fail the ordinary validator.
        element = matches[0]
        inserts.extend([(element['start'], f'<section id="{escape(node_id, quote=True)}" data-node="{escape(node_id, quote=True)}" class="pm-node-anchor">'),
                        (element['end'], '</section>')])
    for offset, text in sorted(inserts, reverse=True):
        value['html'] = value['html'][:offset] + text + value['html'][offset:]
    if not namespace: return value
    # Independent chapter authors often reuse names such as node-output/analysis-text.
    # Rename private identifiers and their literal selector/relation references together.
    mapping = {old: f'{chapter_id}--{old}' for old in scan.ids if old not in node_ids}
    for old, new in sorted(mapping.items(), key=lambda pair: len(pair[0]), reverse=True):
        value['html'] = re.sub(r'(\bid\s*=\s*)([\"\'])' + re.escape(old) + r'\2', lambda m: m[1] + m[2] + new + m[2], value['html'])
        for field in ['html', 'css', 'javascript']:
            value[field] = re.sub(r'#' + re.escape(old) + r'(?![\w-])', '#' + new, value[field])
        for field in ['html', 'javascript']:
            value[field] = re.sub(r'([\"\'`])' + re.escape(old) + r'\1', lambda m: m[1] + new + m[1], value[field])
    return value
