import os
import re
import urllib.parse
from datetime import datetime, timedelta

# --- CONFIGURATION ---
# Using expanduser to handle the '~' and stripping the 'ls ' prefix
obsidian_path = os.getenv("OBSIDIAN_PATH")
vault_path = os.path.expanduser(obsidian_path)
output_folder = os.path.expanduser("~/Documents/obsidian_summary")

# Target Date Selection (Yesterday)
check_dt = datetime.now() - timedelta(days=1) 
# ---------------------

# 1. Prepare Date Strings and Time Windows
target_date_str = check_dt.strftime('%Y-%m-%d')
output_file = os.path.join(output_folder, f"Digest_{target_date_str}.md")

# Window: From start of target day to end of the following day (buffer for late saves)
window_start = datetime.combine(check_dt, datetime.min.time()).timestamp()
window_end = (datetime.combine(check_dt, datetime.max.time()) + timedelta(hours=24)).timestamp()

all_notes = []

# 2. Regex to find the Obsidian header format
pattern = re.compile(
    rf'(#### {target_date_str}, [A-Za-z]+, (\d{{2}}:\d{{2}})[^\n]*)\n(.*?)(?=#### |\Z)', 
    re.DOTALL | re.IGNORECASE
)

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 3. Process Files
for root, dirs, files in os.walk(vault_path):
    for filename in files:
        if filename.endswith(".md"):
            file_path = os.path.join(root, filename)
            
            try:
                # Get modification time
                file_mod_time = os.path.getmtime(file_path)
                
                # Check if file was modified within our target window
                if not (window_start <= file_mod_time <= window_end):
                    continue 

                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    matches = pattern.findall(content)
                    for full_header, time_val, text in matches:
                        # Prepare Obsidian URI
                        vault_name = os.path.basename(vault_path)
                        relative_path = os.path.relpath(file_path, vault_path)
                        encoded_path = urllib.parse.quote(relative_path)
                        obsidian_link = f"obsidian://open?vault={urllib.parse.quote(vault_name)}&file={encoded_path}"
                        
                        all_notes.append({
                            'time': time_val,
                            'header': full_header,
                            'source': filename,
                            'link': obsidian_link,
                            'content': text.strip()
                        })
            except (PermissionError, OSError):
                continue # Skip files that are locked or inaccessible

# 4. Sort Chronologically and Write Output
all_notes.sort(key=lambda x: x['time'])

if all_notes:
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# Daily Digest: {target_date_str}\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n")
        
        for note in all_notes:
            f.write(f"{note['header']}\n")
            f.write(f"*Source: [{note['source']}]({note['link']})*\n\n")
            f.write(f"{note['content']}\n\n---\n\n")
    print(f"✅ Success! Digest created for {target_date_str} at {output_file}")
else:
    print(f"ℹ️ No notes found for {target_date_str} in files modified during that period.")