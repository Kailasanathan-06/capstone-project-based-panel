# API Keys Configuration

SecureDT runs completely offline against synthetic data. **No API keys are
required** for the core product, the Random Forest risk model, or any lab
page.

## Optional External Integrations

The following are optional and never required for the prototype:

| Service | Purpose | Where to configure |
|---|---|---|
| Zeek / Bro | Live network telemetry (replaces simulation) | `config.yaml` → `zeek_logs_dir` |
| Groq Cloud | LLM-assisted plain-language security insight on top of the RF prediction (`AI_PROVIDER=groq`) | `.env` → `GROQ_API_KEY` |

## Groq Cloud LLM Insight Layer (Optional)

To enable the natural-language insight on the AI page:

1. Get a key at <https://console.groq.com> → **API Keys** → **Create API Key**.
2. Edit `SecureDT/.env` (never commit it), set `AI_PROVIDER=groq` and paste
   the key:

   ```ini
   AI_PROVIDER=groq
   GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   GROQ_MODEL=llama-3.3-70b-versatile
   ```

3. Restart the app. The AI page shows a **Groq LLM** status chip and an
   **✨ LLM Insight** button next to **Analyze**.

Behavior notes:
- The LLM layer is strictly additive: the Random Forest remains the fast
  numeric backbone, and `llm_explain()` never runs inside batch/offline
  prediction paths.
- Results are cached (bounded LRU) and every call is timeout-guarded.
- Without a key, `AI_PROVIDER=groq` degrades gracefully to `llm=disabled`
  and the app behaves exactly like `localfeatures`. Set
  `AI_PROVIDER=localfeatures` to run fully offline with no key installed.

## Secret Key

- If `.env` has no `SECRET_KEY`, the app generates a cryptographically
  random 256-bit key (64 hex chars) at startup and **persists it into
  `.env`**, so sessions survive restarts without you choosing one.
- You can also set `SECRET_KEY` yourself in `.env`; it overrides the
  generated value.
- The key is never logged and never appears in any API response.

## Configuration Precedence

1. `.env` (loaded via python-dotenv, optional dependency) and environment
   variables (highest priority): `SECRET_KEY`, `AI_PROVIDER`, `GROQ_API_KEY`,
   `PORT`, `ZEEK_LOGS_DIR`
2. `config.yaml` next to `config.py`
3. Defaults inside `config.py`

Example `config.yaml` (see `config.yaml.example` in the project root):

```yaml
server:
  host: 127.0.0.1
  port: 8000
ga:
  population: 40
  generations: 50
security:
  rate_limit_per_min: 60
data_source:
  label: "SIMULATION DATA"
```

## Security

- Never commit a real API key or `SECRET_KEY` to the repository — `.env` is
  covered by `.gitignore`.
- The app ships a random `SECRET_KEY` per process if none is set; set your
  own in `.env` for persistent sessions.
- All keys are read server-side only and never exposed to the browser.