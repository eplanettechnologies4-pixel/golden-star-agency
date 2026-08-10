import re

html_path = r'c:\Users\Administrator\Desktop\travel-agecny-main\core_admin\templates\dashboard\agent\overview.html'

with open(html_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

content = "".join(lines)

start_pos = content.find('<div class="w-full flex-1 px-4')
end_pos = content.find('</main>')

ws_content = content[start_pos:end_pos]

depth = 0
for match in re.finditer(r'<(/?[a-zA-Z0-9]+)([^>]*)>', ws_content):
    tag = match.group(1).lower()
    attrs = match.group(2)
    
    if tag in ['img', 'input', 'br', 'hr', 'meta', 'link']:
        continue
    if tag.startswith('/'):
        depth -= 1
    else:
        line_num = content[:start_pos + match.start()].count('\n') + 1
        if depth == 1:
            id_m = re.search(r'id=["\']([^"\']+)["\']', attrs)
            id_val = id_m.group(1) if id_m else 'NO_ID'
            has_tab_pane = 'tab-pane' in attrs
            print(f"Line {line_num:4d}: depth={depth} <{tag} id='{id_val}'> is_tab_pane={has_tab_pane}")
        depth += 1
