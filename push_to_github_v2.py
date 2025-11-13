#!/usr/bin/env python
"""
Push files to GitHub repo using direct file creation API.
Works for empty repos.
"""

import os
import sys
import base64
from pathlib import Path

try:
    from github import Github, GithubException
except ImportError:
    print("ERROR: PyGithub not installed.")
    sys.exit(1)

def read_gitignore():
    """Read .gitignore and return a set of patterns to ignore."""
    gitignore_path = Path(".gitignore")
    ignore_patterns = set()
    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    ignore_patterns.add(line)
    return ignore_patterns

def should_ignore(path, ignore_patterns):
    """Check if a path matches any ignore pattern."""
    path_str = str(path)
    for pattern in ignore_patterns:
        if pattern in path_str or path.name == pattern:
            return True
    return False

def collect_files():
    """Collect all files to commit (respecting .gitignore)."""
    ignore_patterns = read_gitignore()
    files = {}
    
    for root, dirs, filenames in os.walk("."):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["venv", "__pycache__"]]
        
        for filename in filenames:
            filepath = Path(root) / filename
            if should_ignore(filepath, ignore_patterns):
                continue
            
            try:
                with open(filepath, "rb") as f:
                    content = f.read()
                github_path = str(filepath).replace("\\", "/").lstrip("./")
                files[github_path] = content
                print(f"  + {github_path}")
            except Exception as e:
                print(f"  ! Skipped {filepath}: {e}")
    
    return files

def main():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN env var not set.")
        sys.exit(1)
    
    owner = "oswin26"
    repo_name = "Invoice-AI-"
    
    print(f"\n📦 Pushing to: https://github.com/{owner}/{repo_name}")
    
    try:
        g = Github(token)
        user = g.get_user()
        print(f"✅ Authenticated as: {user.login}")
    except GithubException as e:
        print(f"ERROR: Auth failed: {e}")
        sys.exit(1)
    
    try:
        repo = user.get_repo(repo_name)
        print(f"✅ Found repo: {repo.full_name}")
    except GithubException:
        print(f"ERROR: Repo not found.")
        sys.exit(1)
    
    print("\n📂 Collecting files...")
    files = collect_files()
    
    if not files:
        print("ERROR: No files to commit.")
        sys.exit(1)
    
    print(f"✅ Found {len(files)} file(s)")
    
    # Create files one by one
    print("\n📝 Creating files in repo...")
    commit_msg = "🚀 Deploy Invoice AI to Streamlit Cloud"
    
    for filepath, content in sorted(files.items()):
        try:
            # Decode if possible, else encode as base64
            try:
                file_content = content.decode("utf-8")
                encoding = None
            except:
                file_content = base64.b64encode(content).decode("utf-8")
                encoding = "base64"
            
            repo.create_file(
                path=filepath,
                message=commit_msg,
                content=file_content,
                branch="main"
            )
            print(f"  ✅ {filepath}")
        except GithubException as e:
            if "409" in str(e) or "exists" in str(e).lower():
                print(f"  ~ {filepath} (already exists)")
            else:
                print(f"  ❌ {filepath}: {e}")
    
    print(f"\n✅ SUCCESS! Repo pushed.")
    print(f"📍 Repository: https://github.com/{owner}/{repo_name}")
    print(f"\n📋 Next steps for Streamlit Cloud:")
    print(f"1. Go to https://streamlit.io/cloud")
    print(f"2. Sign in with GitHub")
    print(f"3. Click 'New app'")
    print(f"4. Select repo: {owner}/{repo_name}, branch: main, file: vision.py")
    print(f"5. Before clicking Deploy, go to Settings → Secrets")
    print(f"   Add: GOOGLE_API_KEY = <your_google_api_key>")
    print(f"6. Click 'Deploy'")
    print(f"7. Wait 1-2 minutes for deployment")

if __name__ == "__main__":
    main()
