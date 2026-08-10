import re

html_path = r'c:\Users\Administrator\Desktop\travel-agecny-main\core_admin\templates\dashboard\agent\overview.html'

with open(html_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

stack = []
void_tags = {'img', 'input', 'br', 'hr', 'meta', 'link'}

for line_no, line in enumerate(lines, 1):
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
                print(f"Line {line_no}: Extra </{closing_tag}> with empty stack")
                continue
            
            if stack[-1]['name'] == closing_tag:
                stack.pop()
            else:
                found_idx = -1
                for i in range(len(stack)-1, -1, -1):
                    if stack[i]['name'] == closing_tag:
                        found_idx = i
                        break
                if found_idx != -1:
                    unclosed = stack[found_idx+1:]
                    for u in unclosed:
                        print(f"Line {line_no}: Tag <{u['name']}> (id={re.search(r'id=[\'\"]([^\'\"]+)', u['attrs'])}) opened at line {u['line']} was skipped before </{closing_tag}>")
                    stack = stack[:found_idx]
                else:
                    print(f"Line {line_no}: Spurious </{closing_tag}>")
