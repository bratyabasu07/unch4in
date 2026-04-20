<p align="center">
  <img src="https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExMzR2YjJqbWtmc3ZwZm1uY2pxdm5zM2xmZmx6czF6cjBvNDFoOGtjYiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/077i6AULCXc0FKTj9s/giphy.gif" width="300"/>
</p>

<h1 align="center">🔓 unch4in</h1>
<h3 align="center"><code>br34k the ch4ins. r34d fr33ly.</code></h3>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-00ff41?style=flat-square&logo=python&logoColor=white&labelColor=0a0a0f"/>
  <img src="https://img.shields.io/badge/FastAPI-0.104-00ff41?style=flat-square&logo=fastapi&logoColor=white&labelColor=0a0a0f"/>
  <img src="https://img.shields.io/badge/TLS-chrome110-00ff41?style=flat-square&labelColor=0a0a0f"/>
  <img src="https://img.shields.io/badge/by-Elliot%20Jr-00ff41?style=flat-square&labelColor=0a0a0f"/>
</p>

---

## 💀 What is unch4in?

A self-hosted **content liberation tool** with a cyberpunk hacker UI.  
Paste ****** restricted article URL → get the **full, unredacted content** — no walls, no limits, no tracking.

### 🔥 Features

```
[+] DUAL ENGINE    — Primary + fallback fetching for 99% uptime  
[+] TLS SPOOF      — Chrome110 fingerprint impersonation via curl_cffi  
[+] GLITCH UI      — Matrix rain, RGB glitch, neon glow aesthetics  
[+] PRIVACY        — Zero tracking, zero cookies, self-hosted  
[+] LAN ACCESS     — Access from phone/tablet on same network  
[+] REST API       — /api/fetch?url=... returns clean JSON  
```

## 🚀 Deploy

```bash
# clone
git clone https://github.com/bratyabasu07/unch4in.git && cd unch4in

# setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# run
python3 main.py

# access
# Local  → http://localhost:8000
# LAN    → http://<YOUR-IP>:8000  (access from phone)
```

## 📡 API

```
GET /                    → Landing page
GET /read?url=<URL>      → Article in hacker UI
GET /api/fetch?url=<URL> → Raw JSON
GET /health              → Status check
```

## 📱 Phone Access

Connect your phone to the same WiFi network and open:
```
http://<your-machine-ip>:8000
```
Find your IP: `hostname -I | awk '{print $1}'`

## 🛠️ Stack

```
├── Backend   → Python, FastAPI, curl_cffi, Jinja2
├── Frontend  → Vanilla HTML/CSS/JS
├── TLS       → Chrome fingerprint impersonation
└── Design    → Cyberpunk / Hacker aesthetic
```

---

<p align="center">
  <code>⚡ crafted by <a href="https://github.com/bratyabasu07">elliot jr aka bratyabasu07</a></code><br/>
  <code>stay curious. stay free. 🔓</code>
</p>
