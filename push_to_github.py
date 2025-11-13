#!/usr/bin/env python
"""
Minimal GitHub repo pusher using PyGithub.
Reads all files in current directory (respecting .gitignore),
creates/pushes to a GitHub repo via the GitHub API.
"""

import os
import sys
from pathlib import Path

try:
    from github import Github, GithubException, InputGitTreeElement
except ImportError:
    print("ERROR: PyGithub not installed. Install with: pip install PyGithub")
    sys.exit(1)

def get_repo_url():
    """Extract owner/repo from HTTPS URL."""
    url = "https://github.com/oswin26/Invoice-AI-.git"
    # Parse: https://github.com/oswin26/Invoice-AI-.git
    parts = url.replace("https://github.com/", "").replace(".git", "").split("/")
    if len(parts) != 2:
        print(f"ERROR: Invalid URL format: {url}")
        sys.exit(1)
    return parts[0], parts[1]

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
        # Skip hidden dirs and venv
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["venv", "__pycache__"]]
        
        for filename in filenames:
            filepath = Path(root) / filename
            if should_ignore(filepath, ignore_patterns):
                continue
            
            # Read file
            try:
                with open(filepath, "rb") as f:
                    content = f.read()
                # Use forward slashes for GitHub
                github_path = str(filepath).replace("\\", "/").lstrip("./")
                files[github_path] = content
                print(f"  + {github_path}")
            except Exception as e:
                print(f"  ! Skipped {filepath}: {e}")
    
    return files

def main():
    """Initialize and push repo to GitHub."""
    
    # Get credentials
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN env var not set.")
        print("Set it with: $env:GITHUB_TOKEN='your_token_here'")
        print("Get a token at: https://github.com/settings/tokens/new")
        sys.exit(1)
    
    owner, repo_name = get_repo_url()
    print(f"\n📦 Pushing to: https://github.com/{owner}/{repo_name}")
    
    # Connect to GitHub
    try:
        g = Github(token)
        user = g.get_user()
        print(f"✅ Authenticated as: {user.login}")
    except GithubException as e:
        print(f"ERROR: Authentication failed: {e}")
        sys.exit(1)
    
    # Get repo
    try:
        repo = user.get_repo(repo_name)
        print(f"✅ Found repo: {repo.full_name}")
    except GithubException:
        print(f"ERROR: Repo {owner}/{repo_name} not found or not accessible.")
        print(f"Make sure the repo exists and your token has 'repo' scope.")
        sys.exit(1)
    
    # Collect files
    print("\n📂 Collecting files...")
    files = collect_files()
    
    if not files:
        print("ERROR: No files to commit.")
        sys.exit(1)
    
    print(f"✅ Found {len(files)} file(s) to commit")
    
    # Create tree elements
    print("\n🔄 Creating Git tree...")
    tree_elements = []
    for filepath, content in files.items():
        element = InputGitTreeElement(
            path=filepath,
            mode="100644",
            type="blob",
            content=content.decode("utf-8", errors="replace")
        )
        tree_elements.append(element)
    
    # Get main branch (or create if doesn't exist)
    try:
        main_branch = repo.get_branch("main")
        base_tree = main_branch.commit.commit.tree
        print(f"✅ Using existing 'main' branch")
    except GithubException:
        try:
            main_branch = repo.get_branch("master")
            base_tree = main_branch.commit.commit.tree
            print(f"✅ Using existing 'master' branch")
        except GithubException:
            # Repo is empty, create initial commit
            base_tree = None
            print(f"✅ Repo is empty, creating initial commit")
    
    # Create tree
    if base_tree:
        tree = repo.create_git_tree(tree_elements, base_tree=base_tree)
    else:
        tree = repo.create_git_tree(tree_elements)
    print(f"✅ Tree created: {tree.sha[:7]}")
    
    # Create commit
    parent_commit = []
    if base_tree is not None:
        try:
            parent_commit = [main_branch.commit]
        except:
            pass
    
    commit_msg = "🚀 Deploy Invoice AI to Streamlit Cloud\n\n- Added vision.py (Streamlit app)\n- Added Dockerfile for containerization\n- Added GitHub Actions CI workflow\n- Added Streamlit config and deployment files"
    
    commit = repo.create_git_commit(
        message=commit_msg,
        tree=tree,
        parents=parent_commit
    )
    print(f"✅ Commit created: {commit.sha[:7]}")
    
    # Update ref
    try:
        repo.get_git_ref("heads/main").edit(commit.sha)
        print(f"✅ Updated main branch to latest commit")
    except GithubException:
        try:
            repo.get_git_ref("heads/master").edit(commit.sha)
            print(f"✅ Updated master branch to latest commit")
        except GithubException:
            # Create new ref
            repo.create_git_ref(ref="refs/heads/main", sha=commit.sha)
            print(f"✅ Created main branch with new commit")
    
    print(f"\n✅ SUCCESS! Repo pushed.")
    print(f"📍 Repository: https://github.com/{owner}/{repo_name}")
    print(f"\nNext steps:")
    print(f"1. Go to https://streamlit.io/cloud")
    print(f"2. Click 'New app'")
    print(f"3. Select repo: {owner}/{repo_name}, branch: main, file: vision.py")
    print(f"4. Add secret: GOOGLE_API_KEY = <your_api_key>")
    print(f"5. Click 'Deploy'")

if __name__ == "__main__":
    main()
