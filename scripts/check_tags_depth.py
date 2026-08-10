import re

html_path = r'c:\Users\Administrator\Desktop\travel-agecny-main\core_admin\templates\dashboard\agent\overview.html'

with open(html_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

stack = []
tab_contents = {}

for idx, line in enumerate(lines, start=1):
    # Find tag openings and closings
    # Match <div or </div> or other container tags
    tokens = re.findall(r'(</?([a-zA-Z0-9]+)(\s+[^>]*)?>)', line)
    for full_tag, tag_name, attrs in tokens:
        tag_name = tag_name.lower()
        if tag_name in ['img', 'br', 'hr', 'input', 'meta', 'link']:
            continue
        if full_tag.startswith('</'):
            if stack:
                popped = stack.pop()
                if popped['tag'] != tag_name:
                    # mismatch
                    pass
            else:
                print(f"Extra closing tag </{tag_name}> at line {idx}")
        elif not full_tag.endswith('/>'):
            tag_id = re.search(r'id=["\']([^"\']+)["\']', attrs) if attrs else None
            tag_id_str = tag_id.group(1) if tag_id else None
            stack.append({'tag': tag_name, 'line': idx, 'id': tag_id_str, 'full': full_tag[:50]})
            if tag_id_str and tag_id_str.startswith('tab-content-'):
                print(f"Opening {tag_id_str} at line {idx}, current stack depth: {len(stack)}")

print(f"Final stack size: {len(stack)}")
if stack:
    print("Unclosed tags remaining in stack:")
    for item in stack[-15:]:
        print(f" - line {item['line']}: <{item['tag']}> id={item['id']}")
