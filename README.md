# bitwarden-skill

A Hermes Agent skill wrapping the BitWarden CLI (`bw`) — non-interactive vault
unlock, secret retrieval, password generation, item CRUD, Send/receive, and
export/import — built for headless terminal automation.

## Credential standard

**The BitWarden master password comes from Apple Keychain** (service
`Bitwarden-Master`), never from `.env` or a password file. `scripts/bw-unlock.sh`
resolves it on every unlock:

```
BW_PASSWORD env override  →  Apple Keychain (Bitwarden-Master)  →  hard error
```

The API-key halves (`Bitworder-ClientID` / `Bitworder-ClientSecret`) live in
Keychain too, for `bw login --apikey`. `--passwordenv` / `--passwordfile` are
documented as non-macOS fallbacks only. See `references/keychain.md` for
one-time setup.

## Layout

```
SKILL.md                  skill definition (When to Use, Prerequisites, Procedures, Pitfalls)
references/
  cli-commands.md         full command/option reference + enum tables
  auth-flow.md            login methods, session lifecycle, unlock patterns
  get-started.md          install, login, unlock, first read, lock
  keychain.md             Keychain service naming, setup, retrieval patterns
  enums.md                item types, URI match types, 2FA methods, field types
  patterns.md             jq + encode pipelines, Send workflows, Keychain patterns
scripts/
  bw-unlock.sh            platform-aware unlock helper (env → Keychain → error)
tests/
  test_bitwarden_skill.py structure tests (no network, no live bw calls)
.env.example              env var reference
```

## Quick start

```bash
# 1. One-time: store the master password in Keychain
security add-generic-password -s "Bitwarden-Master" -w "your-master-password" login.keychain-db

# 2. Log in (first time)
bw login   # or: export BW_CLIENTID=... BW_CLIENTSECRET=... && bw login --apikey

# 3. Unlock + read (every session)
source scripts/bw-unlock.sh && bw get password my-service

# 4. Lock when done
bw lock
```

## Verified against

BitWarden CLI v2026.7.0. Every documented pattern was executed against a live
vault before shipping; the pitfalls section records what actually breaks
(e.g. `.login.uri` strings are silently dropped — use `.login.uris` arrays;
`bw status --raw` is not recognized; `bw report` does not exist).

## Tests

```bash
pytest tests/
```

Structure-only checks: frontmatter, hardlines, no machine-local paths, no
personal data (real emails/tokens), script syntax, documented unlock patterns.

## License

MIT
