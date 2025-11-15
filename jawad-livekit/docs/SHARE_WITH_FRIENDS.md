# Share with Friends - Setup Guide

## The Problem
Your server (chrysler.polytechnique.fr) has a firewall blocking external access to ports 8000 and 8080.

## Solutions for Your Friends

### Option 1: Everyone Uses SSH Tunnel (Most Secure)

Each person needs to:

1. **Have SSH access** to chrysler.polytechnique.fr
2. **Run SSH tunnel**:
   ```bash
   ssh -L 8000:localhost:8000 -L 8080:localhost:8080 jawad.chemaou@chrysler.polytechnique.fr
   ```
3. **Open in browser**: http://localhost:8080/client.html
4. **Join the same room name**

**Pros**: Very secure, no firewall changes needed
**Cons**: Everyone needs SSH access to your server

---

### Option 2: Deploy on a Public Server (Recommended for Hackathon)

Use a service that allows public access:

#### A. Use ngrok (Easiest!)

Install ngrok on the SSH server:
```bash
# Download ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz

# Run ngrok to expose port 8000 (API)
./ngrok http 8000
```

This gives you a public URL like: `https://abc123.ngrok.io`

Update client.html API URL to use the ngrok URL, then share the ngrok link with friends!

#### B. Use Cloudflare Tunnel
```bash
# Install cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x cloudflared-linux-amd64

# Run tunnel
./cloudflared-linux-amd64 tunnel --url http://localhost:8000
```

Gets you a public trycloudflare.com URL!

---

### Option 3: Ask IT to Open Ports (If Allowed)

If you have admin access or can contact IT:

```bash
# Open ports in firewall
sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 8080 -j ACCEPT
sudo iptables-save
```

Then friends can access:
- http://chrysler.polytechnique.fr:8080/client.html
- API: http://chrysler.polytechnique.fr:8000

**Warning**: This exposes your server publicly. Only do this if allowed!

---

### Option 4: Use the Standalone Client (Simplest!)

Share `client-standalone.html` with your friends:

1. **You**: Email/send them the file
2. **They**: Download and open it in their browser
3. **Everyone**: Uses the same room name to connect

**Pros**:
- No server needed
- No SSH needed
- Works from anywhere
- Just share one HTML file

**Cons**:
- Credentials are in the HTML file (less secure)
- No backend analytics

---

## My Recommendation for Hackathon

**Use Option 2A (ngrok)** - It's:
- ✅ Quick to set up (2 minutes)
- ✅ Gives you a public URL
- ✅ Works from anywhere
- ✅ Free for testing
- ✅ HTTPS included

### Quick ngrok Setup:

```bash
# On your SSH server
cd ~/
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz

# Start ngrok for API (port 8000)
./ngrok http 8000
```

You'll see something like:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:8000
```

**That's your public API URL!** Share it with friends.

Then create a new `client-public.html`:
```html
<!-- Change line with apiUrl value to: -->
<input type="text" id="apiUrl" value="https://abc123.ngrok.io" placeholder="https://abc123.ngrok.io">
```

Share that HTML file with friends - they can open it and connect!

---

## Current Status

- ✅ Backend API running on port 8000
- ✅ Web server running on port 8080
- ✅ LiveKit Cloud connected
- ❌ Ports blocked by firewall (can't access externally)

Choose one of the options above to make it accessible to your team!
