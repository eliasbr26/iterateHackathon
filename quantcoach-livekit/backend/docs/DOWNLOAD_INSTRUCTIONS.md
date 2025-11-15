# Download Instructions

The CDN libraries aren't loading through SSH tunnel. Here's the solution:

## Download to Your PC Directly

On **your local PC** (not SSH), download this file:

**Right-click and "Save Link As":**
https://cdn.jsdelivr.net/npm/livekit-client@2.5.8/dist/livekit-client.umd.min.js

Save it as: `livekit-client.umd.min.js`

Then copy the standalone HTML from the server:

```bash
scp jawad.chemaou@129.104.252.67:/users/eleves-b/2022/jawad.chemaou/M2DS/iterateHackathon/jawad-livekit/client-standalone.html ~/Desktop/
```

Edit `client-standalone.html` and change line 7 from:
```html
<script src="https://cdn.jsdelivr.net/npm/livekit-client@2.5.8/dist/livekit-client.umd.min.js"></script>
```

To:
```html
<script src="livekit-client.umd.min.js"></script>
```

Put both files in the same folder and open `client-standalone.html`!

## Or Use the Backend API Instead

Since CDNs aren't working through SSH, let's use the backend API approach:

1. Keep your SSH tunnel open: `ssh -L 8000:localhost:8000 -L 8080:localhost:8080 jawad.chemaou@129.104.252.67`

2. Update the original client.html to use localhost:
   - Change API URL from `http://129.104.252.67:8000` to `http://localhost:8000`

3. Access: http://localhost:8080/client.html

This should work because it goes through your backend API!
