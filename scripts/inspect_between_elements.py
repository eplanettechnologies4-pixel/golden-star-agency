import re

html_path = r'c:\Users\Administrator\Desktop\travel-agecny-main\core_admin\templates\dashboard\agent\overview.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Let's find everything inside <div class="w-full flex-1 px-4 sm:px-6 lg:px-8 pt-0 pb-6 flex flex-col justify-start items-stretch min-w-0 space-y-0">
# and check every direct tag before id="tab-content-contact-us"
start_match = re.search(r'<div class="w-full flex-1 px-4[^>]+>', content)
if start_match:
    start_pos = start_match.end()
    contact_pos = content.find('id="tab-content-contact-us"')
    between = content[start_pos:contact_pos]
    print(f"Length of content between workspace container start and contact-us: {len(between)} bytes")
    
    # Find all top-level IDs in this section
    ids = re.findall(r'<div\s+[^>]*id=["\']([^"\']+)["\']', between)
    print("Found IDs in between:")
    for i in ids:
        print("  -", i)
