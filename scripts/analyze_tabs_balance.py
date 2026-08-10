import re

html_path = r'c:\Users\Administrator\Desktop\travel-agecny-main\core_admin\templates\dashboard\agent\overview.html'

with open(html_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Let's inspect each tab pane start line and end line
tab_starts = []
for idx, line in enumerate(lines, 1):
    m = re.search(r'<div\s+[^>]*id=["\'](tab-content-[^"\']+)["\']', line)
    if m:
        tab_starts.append((idx, m.group(1)))

print("Found tab panes:", len(tab_starts))
for idx, (start_line, tab_id) in enumerate(tab_starts):
    next_line = tab_starts[idx+1][0] if idx+1 < len(tab_starts) else 3325
    print(f"\nAnalyzing {tab_id} (lines {start_line} to {next_line}):")
    
    # Count div balance in this range
    depth = 0
    for l_no in range(start_line, next_line):
        line = lines[l_no - 1]
        for tag in re.finditer(r'<(/?[a-zA-Z0-9]+)[^>]*>', line):
            t = tag.group(1).lower()
            if t == 'div':
                depth += 1
            elif t == '/div':
                depth -= 1
                if depth == 0:
                    print(f"  --> {tab_id} CLOSED at line {l_no}")
    if depth != 0:
        print(f"  [ERROR] {tab_id} finishes with depth = {depth} at line {next_line}!")
