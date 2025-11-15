# SSH Port Forwarding Access Guide

The server ports are blocked by firewall. Use SSH port forwarding to access them!

## Option 1: SSH Port Forwarding (Recommended)

On your **local computer**, run this command:

```bash
ssh -L 8000:localhost:8000 -L 8080:localhost:8080 jawad.chemaou@129.104.252.67
```

Then open in your browser:
- **Client:** http://localhost:8080/client.html
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### What this does:
- Forwards remote port 8000 → your local port 8000
- Forwards remote port 8080 → your local port 8080
- You can then access the servers as if they were running locally

## Option 2: Separate Terminal Windows

If you're already SSH'd in, open **new terminal windows** on your local machine:

### Terminal 1 - Forward API (port 8000):
```bash
ssh -L 8000:localhost:8000 jawad.chemaou@129.104.252.67 -N
```

### Terminal 2 - Forward Web Client (port 8080):
```bash
ssh -L 8080:localhost:8080 jawad.chemaou@129.104.252.67 -N
```

The `-N` flag means "don't execute any commands, just forward ports"

Then open: http://localhost:8080/client.html

## Option 3: VSCode Remote SSH

If you're using VSCode with Remote SSH:

1. Open Command Palette (Ctrl+Shift+P or Cmd+Shift+P)
2. Type "Forward a Port"
3. Add port **8000**
4. Add port **8080**
5. Open http://localhost:8080/client.html in your browser

## Option 4: Update client.html for localhost

Since you'll be accessing via SSH tunnel, update the API URL:

```bash
# The client.html will automatically use http://129.104.252.67:8000
# But you need to change it to localhost when using SSH tunnel
```

Let me create a localhost version:

## Testing the Setup

Once you have SSH tunnels set up:

### Test 1: Check API
```bash
# On your local machine (with tunnel active)
curl http://localhost:8000/
```

Should return:
```json
{"status":"ok","service":"LiveKit Interview API","version":"1.0.0"}
```

### Test 2: Access Client
Open: http://localhost:8080/client.html

### Test 3: Create a room
```bash
curl -X POST http://localhost:8000/rooms/create \
  -H "Content-Type: application/json" \
  -d '{"max_participants": 10}'
```

## Quick Start (All-in-One)

**On your local machine**, run:

```bash
# Start SSH with port forwarding (stay connected)
ssh -L 8000:localhost:8000 -L 8080:localhost:8080 jawad.chemaou@129.104.252.67

# Keep this terminal open, then in your browser open:
# http://localhost:8080/client.html
```

## For Team Testing

Each team member needs to:

1. Have SSH access to the server
2. Run the SSH tunnel command above
3. Open http://localhost:8080/client.html
4. All connect to the same room name

Or alternatively, you can ask your IT/admin to open ports 8000 and 8080 in the firewall.

## Firewall Information

If you have sudo access, you can try opening the ports:

```bash
# Check current firewall status
sudo iptables -L -n

# Open ports (if you have permission)
sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 8080 -j ACCEPT

# Save rules (depends on your system)
sudo iptables-save
```

But SSH tunneling is safer and doesn't require firewall changes!
