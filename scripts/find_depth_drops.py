import re

html_path = r'c:\Users\Administrator\Desktop\travel-agecny-main\core_admin\templates\dashboard\agent\overview.html'

with open(html_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

content = "".join(lines)
start_pos = content.find('<div class="w-full flex-1 px-4')
end_pos = content.find('</main>')
ws_content = content[start_pos:end_pos]

stack = []

for line_idx, line in enumerate(ws_content.split('\n'), start=content[:start_pos].count('\n') + 1):
    for match in re.finditer(r'<(/?[a-zA-Z0-9]+)([^>]*)>', line):
        tag = match.group(1).lower()
        attrs = match.group(2)
        
        if tag in ['img', 'input', 'br', 'hr', 'meta', 'link']:
            continue
            
        if tag.startswith('/'):
            if stack:
                stack.pop()
            else:
                print(f"Line {line_idx:4d}: EXTRA CLOSING </{tag[1:]}>")
        else:
            id_m = re.search(r'id=["\']([^"\']+)["\']', attrs)
            id_val = id_m.group(1) if id_m else ''
            is_tab = 'tab-pane' in attrs
            if is_tab:
                print(f"Line {line_idx:4d}: TAB-PANE {id_val} opens at current stack depth = {len(stack)}")
            stack.append({'tag': tag, 'id': id_val, 'line': line_idx})
