import os
import re

html_path = r'c:\Users\Administrator\Desktop\travel-agecny-main\core_admin\templates\dashboard\agent\overview.html'

with open(html_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Let's track exact tag nesting line by line
stack = []
void_tags = {'img', 'input', 'br', 'hr', 'meta', 'link'}

for line_no, line in enumerate(lines, 1):
    # Regex to find all tags
    for m in re.finditer(r'<(/?[a-zA-Z0-9]+)([^>]*)>', line):
        tag_str = m.group(0)
        tag_name = m.group(1).lower()
        attrs = m.group(2)
        
        if tag_name in void_tags or tag_str.endswith('/>'):
            continue
            
        if tag_name.startswith('/'):
            closing_tag = tag_name[1:]
            if closing_tag in void_tags:
                continue
            if not stack:
                print(f"Line {line_no}: Unexpected closing tag </{closing_tag}> with empty stack!")
                continue
            
            # Check top of stack
            if stack[-1]['name'] == closing_tag:
                stack.pop()
            else:
                # Find if closing_tag exists further down
                found_idx = -1
                for i in range(len(stack)-1, -1, -1):
                    if stack[i]['name'] == closing_tag:
                        found_idx = i
                        break
                if found_idx != -1:
                    # Unclosed tags between found_idx and top
                    unclosed = stack[found_idx+1:]
                    for u in unclosed:
                        print(f"Line {line_no}: Tag <{u['name']}> opened at line {u['line']} was never closed before </{closing_tag}> (attrs: {u['attrs'][:60]})")
                    stack = stack[:found_idx]
                else:
                    print(f"Line {line_no}: Spurious closing tag </{closing_tag}> not matching any open tag!")
        else:
            stack.append({'name': tag_name, 'line': line_no, 'attrs': attrs})

print(f"\nRemaining unclosed tags at end of document ({len(stack)}):")
for u in stack:
    print(f" - Line {u['line']}: <{u['name']}> ({u['attrs'][:60]})")
