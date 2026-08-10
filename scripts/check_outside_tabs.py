import re

html_path = r'c:\Users\Administrator\Desktop\travel-agecny-main\core_admin\templates\dashboard\agent\overview.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

start_pos = content.find('<div class="w-full flex-1 px-4')
end_pos = content.find('</main>')

ws_content = content[start_pos:end_pos]

# Let's track which tab_pane is active for each line
current_tab_pane = None
tab_pane_stack = []

for line_idx, line in enumerate(ws_content.split('\n'), start=content[:start_pos].count('\n') + 1):
    for match in re.finditer(r'<(/?[a-zA-Z0-9]+)([^>]*)>', line):
        tag = match.group(1).lower()
        attrs = match.group(2)
        
        if tag in ['img', 'input', 'br', 'hr', 'meta', 'link']:
            continue
            
        if tag.startswith('/'):
            if tab_pane_stack:
                tab_pane_stack.pop()
        else:
            if 'tab-pane' in attrs:
                id_m = re.search(r'id=["\']([^"\']+)["\']', attrs)
                tab_id = id_m.group(1) if id_m else 'UNKNOWN_TAB'
                tab_pane_stack.append({'tag': tag, 'tab_id': tab_id, 'line': line_idx})
                print(f"Line {line_idx:4d}: ENTERED TAB-PANE: {tab_id}")
            else:
                if tab_pane_stack:
                    tab_pane_stack.append({'tag': tag, 'tab_id': tab_pane_stack[-1]['tab_id'], 'line': line_idx})
                else:
                    if tag == 'div' and not any(k in attrs for k in ['tab-loader', 'messages', 'space-y-2']):
                        print(f"Line {line_idx:4d}: TAG OUTSIDE ANY TAB-PANE! <{tag} {attrs[:50]}>")

print(f"Final tab stack depth: {len(tab_pane_stack)}")
