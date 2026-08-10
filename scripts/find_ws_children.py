import re

html_path = r'c:\Users\Administrator\Desktop\travel-agecny-main\core_admin\templates\dashboard\agent\overview.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

start_pos = content.find('<main')
end_pos = content.find('</main>')
main_html = content[start_pos:end_pos]

# Find all direct children of the workspace div
ws_match = re.search(r'<div class="w-full flex-1[^>]+>', main_html)
ws_start = ws_match.end()

ws_content = main_html[ws_start:]

# Let's find every top level tag inside ws_content
depth = 0
for match in re.finditer(r'<(/?[a-zA-Z0-9]+)([^>]*)>', ws_content):
    tag = match.group(1).lower()
    attrs = match.group(2)
    
    if tag in ['img', 'input', 'br', 'hr', 'meta', 'link']:
        continue
    if tag.startswith('/'):
        depth -= 1
    else:
        if depth == 0:
            # Top level child of workspace div!
            has_tab_pane = 'tab-pane' in attrs
            id_m = re.search(r'id=["\']([^"\']+)["\']', attrs)
            id_val = id_m.group(1) if id_m else 'NO_ID'
            print(f"Top-level child: <{tag} id='{id_val}'> is_tab_pane={has_tab_pane}")
        depth += 1
