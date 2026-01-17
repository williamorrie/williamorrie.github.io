import os
import re
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

# --- CONFIGURATION ---
obsidian_vault = Path(os.getenv("OBSIDIAN_VAULT"))
input_folder = obsidian_vault / "2021-08-29_All_Evernote"
output_folder = obsidian_vault / "_digests"

# Target Date Selection (Yesterday)
check_dt = datetime.now() - timedelta(days=2)
# ---------------------

# 1. Prepare Date Strings and Time Windows
target_date_str = check_dt.strftime("%Y-%m-%d")
target_day = check_dt.strftime("%a").upper()
output_file = output_folder / f"{target_date_str}_{target_day}_Digest.md"

# Only process files modified on or after the target date
min_mod_time = datetime.combine(check_dt, datetime.min.time()).timestamp()

all_notes = []

# 2. Regex to find the Obsidian header format
pattern = re.compile(
    rf"(#### {target_date_str}, [A-Za-z]+, (\d{{2}}:\d{{2}})[^\n]*)\n(.*?)(?=^#### |\Z)",
    re.DOTALL | re.IGNORECASE | re.MULTILINE,
)

output_folder.mkdir(parents=True, exist_ok=True)

# 3. Process Files
files_checked = 0
files_in_time_range = 0
for file_path in input_folder.rglob("*.md"):
    files_checked += 1

    try:
        # Get modification time
        file_mod_time = file_path.stat().st_mtime

        # Check if file was modified on or after the target date
        if file_mod_time < min_mod_time:
            continue

        files_in_time_range += 1

        content = file_path.read_text(encoding="utf-8")
        matches = pattern.findall(content)
        for full_header, time_val, text in matches:
            # Prepare Obsidian URI
            vault_name = input_folder.name
            relative_path = file_path.relative_to(input_folder)
            encoded_path = urllib.parse.quote(str(relative_path))
            obsidian_link = f"obsidian://open?vault={urllib.parse.quote(vault_name)}&file={encoded_path}"

            all_notes.append(
                {
                    "time": time_val,
                    "header": full_header,
                    "source": file_path.name,
                    "link": obsidian_link,
                    "content": text.strip(),
                }
            )
    except (PermissionError, OSError):
        continue  # Skip files that are locked or inaccessible

# 4. Sort Chronologically and Write Output
all_notes.sort(key=lambda x: x["time"])

if all_notes:
    # Calculate statistics
    unique_files = len(set(note["source"] for note in all_notes))
    total_entries = len(all_notes)
    word_counts = [len(note["content"].split()) for note in all_notes]
    total_words = sum(word_counts)
    first_entry = all_notes[0]["time"]
    last_entry = all_notes[-1]["time"]
    avg_words = total_words // total_entries if total_entries > 0 else 0
    min_words = min(word_counts) if word_counts else 0
    max_words = max(word_counts) if word_counts else 0

    # Find file with most edits
    file_counts = {}
    for note in all_notes:
        file_counts[note["source"]] = file_counts.get(note["source"], 0) + 1
    most_edited_file = max(file_counts.items(), key=lambda x: x[1])

    # Find hour with most entries
    hour_counts = {}
    for note in all_notes:
        hour = note["time"].split(":")[0]
        hour_counts[hour] = hour_counts.get(hour, 0) + 1
    busiest_hour = max(hour_counts.items(), key=lambda x: x[1])

    content_lines = [f"# Daily Digest: {target_date_str}\n\n"]
    content_lines.append(
        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    )

    # Add statistics
    content_lines.append("## Summary Statistics\n\n")
    content_lines.append(f"- **Files edited**: {unique_files}\n")
    content_lines.append(f"- **Total entries**: {total_entries}\n")
    content_lines.append(f"- **Total words**: {total_words:,}\n")
    content_lines.append(
        f"- **Words per entry**: avg={avg_words}, min={min_words}, max={max_words}\n"
    )
    content_lines.append(f"- **Time span**: {first_entry} - {last_entry}\n")
    content_lines.append(
        f"- **Most edited file**: {most_edited_file[0]} ({most_edited_file[1]} entries)\n"
    )
    content_lines.append(
        f"- **Busiest hour**: {busiest_hour[0]}:00 ({busiest_hour[1]} entries)\n"
    )
    content_lines.append("\n---\n\n")

    for note in all_notes:
        content_lines.append(f"{note['header']}\n")
        content_lines.append(f"*Source: [{note['source']}]({note['link']})*\n\n")
        content_lines.append(f"{note['content']}\n\n---\n\n")

    output_file.write_text("".join(content_lines), encoding="utf-8")
    print(f"✅ Success! Digest created for {target_date_str} at {output_file}")
else:
    print(
        f"ℹ️ No notes found for {target_date_str} in files modified during that period."
    )
    print(
        f"   Files checked: {files_checked}, Files in time range: {files_in_time_range}"
    )
