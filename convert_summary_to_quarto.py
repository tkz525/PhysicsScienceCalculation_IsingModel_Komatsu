import re
import os
import shutil

src_dir = r"c:\Users\Ikeda\Desktop\PhysicsScienceCalculation\rust-computational-physics-tutorial-main\src"
# Copy README.md to index.md if index.md doesn't exist
readme_path = os.path.join(src_dir, "README.md")
index_path = os.path.join(src_dir, "index.md")
shutil.copy(readme_path, index_path)
print(f"Copied {readme_path} to {index_path}")

chapters = ["index.md"]
current_part = None

summary_path = os.path.join(src_dir, "SUMMARY.md")
with open(summary_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for line in lines:
    # We keep spaces for indentation checking, but strip trailing newline
    line = line.rstrip()
    if not line.strip():
        continue
    
    # Check for part header: # 第1部: 基礎編
    part_match = re.match(r"^#\s+(.+)", line.strip())
    if part_match:
        part_title = part_match.group(1)
        if part_title.lower() != "summary":
            # Start a new part
            if current_part:
                chapters.append(current_part)
            current_part = {"part": part_title, "chapters": []}
        continue
        
    # Check for links: - [Rustと計算物理学](./ch01-introduction/README.md)
    # Or sub-links with leading spaces
    link_match = re.match(r"^(\s*)-\s+\[([^\]]+)\]\(([^)]+)\)", line)
    if link_match:
        indent = link_match.group(1)
        title = link_match.group(2)
        path = link_match.group(3)
        
        # Normalize path: remove leading `./`
        path = re.sub(r"^\./", "", path)
        
        if path == "README.md":
            # This is "はじめに", already handled as index.md
            continue
            
        if current_part:
            current_part["chapters"].append(path)
        else:
            chapters.append(path)

if current_part:
    chapters.append(current_part)

# Generate YAML content manually to avoid dependency on PyYAML
yaml_lines = []
yaml_lines.append("project:")
yaml_lines.append("  type: book")
yaml_lines.append("  output-dir: ../book_html")
yaml_lines.append("")
yaml_lines.append("book:")
yaml_lines.append('  title: "Rust計算物理学チュートリアル"')
yaml_lines.append('  author: "sakuraba07, 品岡寛"')
yaml_lines.append("  language: ja")
yaml_lines.append("  chapters:")

for item in chapters:
    if isinstance(item, str):
        yaml_lines.append(f"    - {item}")
    elif isinstance(item, dict):
        yaml_lines.append(f"    - part: \"{item['part']}\"")
        yaml_lines.append("      chapters:")
        for ch in item["chapters"]:
            yaml_lines.append(f"        - {ch}")
            
yaml_lines.append("")
yaml_lines.append("format:")
yaml_lines.append("  html:")
yaml_lines.append("    theme: cosmo")
yaml_lines.append("    toc: true")
yaml_lines.append("    number-sections: true")

q_yml_path = os.path.join(src_dir, "_quarto.yml")
with open(q_yml_path, "w", encoding="utf-8") as f:
    f.write("\n".join(yaml_lines))

print(f"Generated {q_yml_path} successfully!")
