# VIP NUMBER LAB PRO — Android beginner setup

## Ye project kya karta hai?
- Mobile-friendly website
- Flask backend/API
- Manual historical result entry (period ID + number 0–9)
- Frequency dashboard, CSV export, Big/Small label (0–4 Small, 5–9 Big)
- Walk-forward backtest for top 1/2/3 historical-frequency candidates
- Optional Telegram bot commands: `/start`, `/help`, `/stats`, `/recent`, `/add PERIOD_ID NUMBER`

**Limit:** Ye 91 Club se connect nahi hota, hidden/server results access nahi karta aur sure-shot prediction nahi deta. Data manually enter hota hai. Standard local SQLite database may not persist on every cloud host/redeploy; for long-term production storage, use a managed PostgreSQL database and adjust the app.

## A. Deploy website/backend (phone se)
1. Phone browser mein https://github.com par account banao/sign in karo.
2. New repository banao, e.g. `vip-number-lab-pro`. Public repo convenient hai; is project mein secret/token hard-code mat karna.
3. Is ZIP ko unzip karke saari files repo mein upload karo. GitHub website par **Add file → Upload files** use kar sakte ho.
4. https://render.com par sign up karo aur GitHub connect karo.
5. Render dashboard mein **New → Web Service** choose karo, repo select karo.
6. Build command: `pip install -r requirements.txt`
7. Start command: `gunicorn app:app --workers 1 --threads 4 --timeout 120`
8. Deploy. Deployment ke baad Render URL kholna. `/health` endpoint par `{"ok":true,...}` aana chahiye.
9. Free hosting may sleep and local files may be ephemeral. 24/7 uptime and persistent data may require a paid always-on service plus managed database. Do not rely on local SQLite for important long-term data.

## B. Telegram bot create karna
1. Telegram app mein verified `@BotFather` account search karo.
2. Send `/newbot`.
3. Bot ka display name enter karo, e.g. `VIP Number Lab`.
4. Unique username enter karo jo `bot` par end ho, e.g. `vip_number_lab_example_bot` (agar available ho).
5. BotFather token dega. **Token chat mein, screenshot mein, ya GitHub code mein mat bhejna.** Use private rakho.
6. Render dashboard → your service → **Environment** → add variable:
   - Key: `TELEGRAM_BOT_TOKEN`
   - Value: BotFather ka token
7. Save changes/redeploy. Bot ke Telegram chat ko open karke `/start` bhejo.
8. Bot commands:
   - `/stats`
   - `/recent`
   - `/add 11009 7` (example only: save a completed round)
9. Bot ko private chat mein use karna easiest hai. Public group mein add karne se pehle access-control features add karna recommended hai.

## C. Important production notes
- This starter bot accepts `/add` from anyone who can message it. Before using it in a public group or sharing widely, add an allowed-user-ID check.
- For persistent history, configure managed PostgreSQL or a persistent disk. SQLite on ephemeral hosting can lose data on redeploy/restart.
- For reliable 24/7 bot service, consider a dedicated worker service; the included polling bot runs in the web process for beginner simplicity and should use a single instance only.
- Do not put Telegram tokens in frontend code or commit them to GitHub.
- The statistics are descriptive and historical. They do not guarantee future numbers, winning, or profit.
