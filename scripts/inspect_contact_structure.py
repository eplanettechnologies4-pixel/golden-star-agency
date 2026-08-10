import os
import re

html_path = r'c:\Users\Administrator\Desktop\travel-agecny-main\core_admin\templates\dashboard\agent\overview.html'

with open(html_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Search for all elements between line 470 and line 1910
for idx, line in enumerate(lines[465:1915], start=466):
    if 'id=' in line or 'class=' in line and ('tab-pane' in line or 'style' in line or 'min-h' in line or 'h-' in line):
        print(f"Line {idx}: {line.strip()[:100]}")
