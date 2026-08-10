import re

html_path = r'c:\Users\Administrator\Desktop\travel-agecny-main\core_admin\templates\dashboard\agent\overview.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the workspace container start and closing </main>
start_idx = content.find('<div class="w-full flex-1 px-4')
main_end_idx = content.find('</main>')

workspace_html = content[start_idx:main_end_idx]

# Let's parse all top-level divs inside workspace_html by tracking depth
depth = 0
current_tag = None
top_level_elements = []

# Tokenize tags
pos = 0
for match in re.finditer(r'<(/?[a-zA-Z0-9]+)(\s+[^>]*)?>', workspace_html):
    full = match.group(0)
    tag = match.group(1).lower()
    attrs = match.group(2) or ''
    
    if tag.startswith('/'):
        clean_tag = tag[1:]
        if clean_tag in ['img', 'br', 'hr', 'input']:
            continue
        depth -= 1
    else:
        if tag in ['img', 'br', 'hr', 'input', 'meta', 'link'] or full.endswith('/>'):
            continue
        if depth == 1: # direct child of workspace div
            id_match = re.search(r'id=["\']([^"\']+)["\']', attrs)
            class_match = re.search(r'class=["\']([^"\']+)["\']', attrs)
            top_level_elements.append({
                'tag': tag,
                'id': id_match.group(1) if id_match else 'NO_ID',
                'class': class_match.group(1) if class_match else 'NO_CLASS',
                'line': content[:start_idx + match.start()].count('\n') + 1
            })
        depth += 1

print(f"Total top-level elements inside workspace container: {len(top_level_elements)}")
for el in top_level_elements:
    print(f"Line {el['line']}: <{el['tag']} id='{el['id']}'> class='{el['class']}'")
