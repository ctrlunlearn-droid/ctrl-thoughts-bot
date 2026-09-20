# ctrl_thoughts_ carousel bot

Roz 1 Instagram carousel (7-8 slides, Hinglish) apne aap banata aur post karta hai. Sab free.
Niche roz rotate hota hai: finance -> fitness -> motivation.

Flow: Gemini content likhta hai -> Playwright slides banata hai -> images GitHub repo mein
push hoti hain (public URL) -> Instagram API se post -> images delete, history save.

## Setup (ek baar)

### 1. Gemini API key
aistudio.google.com par login -> "Get API key" -> key copy karo.

### 2. Instagram + Meta app
1. Instagram ko Business ya Creator account mein switch karo (Settings -> Account type).
2. developers.facebook.com par developer account banao -> Create App.
3. App mein "Instagram" product add karo -> "API setup with Instagram login".
4. Apna Instagram account (tester/role ke roop mein) add karo aur `instagram_business_basic` +
   `instagram_business_content_publish` permissions ke saath token generate karo.
5. Wahin se **Instagram User ID** aur **Access Token** milega.
6. Agar token short-lived hai to usko long-lived (60 din) banao. Meta docs mein
   "long-lived token" section dekho. Dashboard ka UI badalta rehta hai, isliye docs se verify karo.

### 3. GitHub repo
1. Naya **public** repo banao (public zaroori hai, warna Instagram images fetch nahi kar payega).
2. Ye poora folder us repo mein push karo.
3. Repo -> Settings -> Secrets and variables -> Actions -> New repository secret:
   - `GEMINI_API_KEY`
   - `IG_USER_ID`
   - `IG_ACCESS_TOKEN`
4. Settings -> Actions -> General -> Workflow permissions -> **Read and write permissions** ON.

### 4. Pehle test karo (post nahi hoga)
Actions tab -> "Daily carousel post" -> Run workflow (dry_run = ON). Run khatam hone par
artifact `slides-preview` download karke slides dekh lo.

Jab slides pasand aayein, dry_run OFF karke ek baar manually chalao. Post live ho jayega.
Uske baad roz 7:30 PM IST par apne aap chalega.

## Local test (optional)
```
pip install -r requirements.txt
python -m playwright install chromium
cp .env.example .env      # GEMINI_API_KEY bharo
python main.py dry-run    # slides ./out mein banenge
```

## Token expiry (zaroori)
Instagram token 60 din mein expire hota hai. Do raaste:
- **Manual:** har ~50 din mein `python refresh_token.py` chalao aur GitHub secret update karo.
- **Auto:** GitHub par ek Personal Access Token (fine-grained, sirf is repo par "Secrets: read and write")
  banao aur `GH_PAT` naam se secret save karo. `refresh-token.yml` har 2 hafte mein token refresh kar dega.

## Customize
- Post ka time: `.github/workflows/daily-post.yml` mein `cron` (UTC mein; IST = UTC + 5:30).
- Niche force karna: env `NICHE=finance`.
- Design: `render.py` (colors `ACCENTS`, fonts CSS mein).
- Content ka style/rules: `generate.py` mein `NICHES` aur `_prompt`.

## Dhyan rakho
- Gemini free tier ki limits badalti rehti hain. Zyada requests par 429 aa sakta hai (code retry karta hai).
- GitHub Actions ka schedule kabhi 10-20 min late ho sakta hai.
- Finance/fitness captions mein disclaimer automatic judta hai.
- Public repo mein sirf history.json (topics ki list) rehti hai. Secrets kabhi code mein mat daalna.
