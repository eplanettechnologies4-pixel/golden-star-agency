import html.parser

html_path = r'c:\Users\Administrator\Desktop\travel-agecny-main\core_admin\templates\dashboard\agent\overview.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

class TagParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.tabs = {}
        self.errors = []
        self.void_tags = {'img', 'input', 'br', 'hr', 'meta', 'link'}
        
    def handle_starttag(self, tag, attrs):
        if tag in self.void_tags:
            return
        attrs_dict = dict(attrs)
        tag_id = attrs_dict.get('id', '')
        tag_class = attrs_dict.get('class', '')
        
        self.stack.append({
            'tag': tag,
            'id': tag_id,
            'class': tag_class,
            'line': self.getpos()[0]
        })
        
        if tag_id.startswith('tab-content-'):
            self.tabs[tag_id] = {
                'start_line': self.getpos()[0],
                'start_depth': len(self.stack),
                'closed': False,
                'end_line': None
            }
            
    def handle_endtag(self, tag):
        if tag in self.void_tags:
            return
        if not self.stack:
            self.errors.append(f"Line {self.getpos()[0]}: Spurious </{tag}> with empty stack")
            return
        popped = self.stack.pop()
        if popped['id'] and popped['id'] in self.tabs:
            self.tabs[popped['id']]['closed'] = True
            self.tabs[popped['id']]['end_line'] = self.getpos()[0]

parser = TagParser()
parser.feed(content)

print(f"Parsed {len(parser.tabs)} tab-panes:")
for tid, info in parser.tabs.items():
    print(f" - {tid:30} : start={info['start_line']:4d}, end={str(info['end_line']):4s}, closed={info['closed']}, start_depth={info['start_depth']}")

print(f"\nTotal unclosed tags left on stack: {len(parser.stack)}")
for item in parser.stack:
    if item['tag'] != 'html' and item['tag'] != 'body':
        print(f"  Line {item['line']:4d}: <{item['tag']} id='{item['id']}' class='{item['class'][:40]}'>")
