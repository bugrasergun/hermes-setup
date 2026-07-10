#!/usr/bin/env python3
# OKF Bundle Validator
# Validates directory format, YAML frontmatter existence, type field presence, and cross-linking syntax.
# Standard library only (no external dependencies like PyYAML).

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESERVED = ['index.md', 'log.md']

def parse_simple_yaml(yaml_text):
    """Simple regex-based YAML parser for key-value pairs."""
    data = {}
    lines = yaml_text.strip().split('\n')
    for line in lines:
        if not line.strip() or line.strip().startswith('#'):
            continue
        match = re.match(r'^([a-zA-Z0-9_\-]+)\s*:\s*(.*)$', line.strip())
        if match:
            key = match.group(1).strip()
            value = match.group(2).strip()
            # Strip quotes if present
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            data[key] = value
    return data

def validate_conformance():
    errors = []
    warnings = []
    concepts = 0

    print(f"Scanning directory: {ROOT}")
    
    for root_dir, dirs, files in os.walk(ROOT):
        # Skip git directory and obsidian config
        if '.git' in root_dir or '.obsidian' in root_dir:
            continue
            
        for file in files:
            if not file.endswith('.md'):
                continue
                
            file_path = os.path.join(root_dir, file)
            rel_path = os.path.relpath(file_path, ROOT)
            
            if file in RESERVED:
                # Reserved files should not have frontmatter
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                if content.strip().startswith('---'):
                    # Root index.md is allowed okf_version frontmatter
                    if rel_path == 'index.md':
                        try:
                            fm_content = content.split('---')[1]
                            fm = parse_simple_yaml(fm_content)
                            if not fm or 'okf_version' not in fm:
                                errors.append(f"{rel_path}: Root index.md frontmatter can only contain okf_version")
                        except Exception as e:
                            errors.append(f"{rel_path}: Malformed frontmatter in root index.md: {e}")
                    else:
                        errors.append(f"{rel_path}: Reserved file must NOT contain YAML frontmatter")
                continue
                
            concepts += 1
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Verify YAML Frontmatter
            if not content.startswith('---'):
                errors.append(f"{rel_path}: Missing frontmatter block at start")
                continue
                
            parts = content.split('---', 2)
            if len(parts) < 3:
                errors.append(f"{rel_path}: Unclosed or invalid frontmatter block")
                continue
                
            frontmatter_raw = parts[1]
            body = parts[2]
            
            # Parse YAML
            try:
                fm = parse_simple_yaml(frontmatter_raw)
            except Exception as e:
                errors.append(f"{rel_path}: YAML parse failure: {e}")
                continue
                
            if not fm:
                errors.append(f"{rel_path}: Frontmatter is empty or malformed")
                continue
                
            # 1. Check type field presence
            if 'type' not in fm or not fm['type']:
                errors.append(f"{rel_path}: REQUIRED field 'type' is missing or empty")
                
            # 2. Recommended fields warnings
            if 'description' not in fm:
                warnings.append(f"{rel_path}: Recommended field 'description' is missing")
            elif fm['description']:
                desc = fm['description'].strip()
                # Check for single sentence roughly
                sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', desc)
                if len(sentences) > 1:
                    warnings.append(f"{rel_path}: Field 'description' should ideally be a single sentence")
                    
            # 3. Check for absolute links starting with /
            absolute_links = re.findall(r'\[.*?\]\((\/.*?\.md)\)', body)
            if absolute_links:
                warnings.append(f"{rel_path}: Contains absolute links starting with '/' ({absolute_links}). Relative paths preferred to prevent breaking on GitHub.")

    print(f"\n--- Validation Summary ---")
    print(f"Validated concepts: {concepts}")
    print(f"Errors found: {len(errors)}")
    print(f"Warnings found: {len(warnings)}")
    
    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  [WARN] {w}")
            
    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  [ERROR] {e}")
        return False
        
    print("\n✓ Bundle is OKF v0.1 Conformant!")
    return True

if __name__ == '__main__':
    success = validate_conformance()
    if not success:
        sys.exit(1)
