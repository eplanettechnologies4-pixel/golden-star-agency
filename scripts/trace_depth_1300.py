import html.parser

html_path = r'c:\Users\Administrator\Desktop\travel-agecny-main\core_admin\templates\dashboard\agent\overview.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

class DepthTracer(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.void_tags = {'img', 'input', 'br', 'hr', 'meta', 'link'}
        
    def handle_starttag(self, tag, attrs):
        if tag in self.void_tags:
            return
        attrs_dict = dict(attrs)
        self.stack.append({'tag': tag, 'id': attrs_dict.get('id', ''), 'class': attrs_dict.get('class', ''), 'line': self.getpos()[0]})
        if self.getpos()[0] >= 1300 and self.getpos()[0] <= 1330:
            print(f"Line {self.getpos()[0]:4d}: <{tag} id='{attrs_dict.get('id', '')}'> depth now {len(self.stack)}")
            
    def handle_endtag(self, tag):
        if tag in self.void_tags:
            return
        if not self.stack:
            return
        popped = self.stack.pop()
        if self.getpos()[0] >= 1300 and self.getpos()[0] <= 1330:
            print(f"Line {self.getpos()[0]:4d}: </{tag}> (closed <{popped['tag']} id='{popped['id']}'> opened at line {popped['line']}), depth now {len(self.stack)}")

tracer = DepthTracer()
tracer.feed(content)
