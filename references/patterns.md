# BitWarden CLI Patterns

## macOS Keychain Password Retrieval

Use the `security` CLI (built into macOS) to store and retrieve BitWarden credentials from Apple Keychain without ever putting them in `.env` or a password file. Cross-reference: `apple-keychain` skill.

### Keychain service naming convention

| Keychain service name | Stores |
|---|---|
| `Bitwarden-Master` | Master password (plaintext) |
| `Bitwarden-ClientID` | API key client_id |
| `Bitwarden-ClientSecret` | API key client_secret |
| `Bitwarden-BW_SESSION` | Cached session key (may be expired) |

### One-time setup: store credentials in Keychain

```bash
# Store master password (one-time)
security add-generic-password -s "Bitwarden-Master" -w "YOUR_MASTER_PASSWORD" login.keychain-db

# Store API key credentials (for non-interactive auth)
security add-generic-password -s "Bitwarden-ClientID" -w "user.xxx-xxx" login.keychain-db
security add-generic-password -s "Bitwarden-ClientSecret" -w "your-secret" login.keychain-db
```

### Unlock vault using Keychain-retrieved master password

```bash
# Retrieve master password from Keychain and unlock in one pipeline
export BW_PASSWORD="$(security find-generic-password -s "Bitwarden-Master" -w)"
export BW_SESSION="$(bw unlock --passwordenv BW_PASSWORD --raw)"

# Now run vault commands
bw list items --pretty | jq '.[].name'
bw get password "GitHub" --raw
```

### Non-interactive auth using Keychain-stored API key

```bash
# API key auth (no master password needed, but you still need BW_PASSWORD to unlock)
export BW_CLIENTID="$(security find-generic-password -s "Bitwarden-ClientID" -w)"
export BW_CLIENTSECRET="$(security find-generic-password -s "Bitwarden-ClientSecret" -w)"
bw login --apikey --nointeraction && bw unlock --passwordenv BW_PASSWORD --raw
```

### Try cached session key first, fall back to unlock

```bash
# Check if cached session from Keychain is still valid
export BW_SESSION="$(security find-generic-password -s "Bitworder-BW_SESSION" -w 2>/dev/null)"
if [ "$(bw status 2>/dev/null | jq -r '.status // empty' 2>/dev/null)" = "unlocked" ]; then
  echo "Session valid"
else
  # Session expired — unlock fresh from Keychain master password
  export BW_PASSWORD="$(security find-generic-password -s "Bitwarden-Master" -w)"
  export BW_SESSION="$(bw unlock --passwordenv BW_PASSWORD --raw)"
fi
```

**Why this is better than .env:** Keychain is encrypted by the macOS user session and accessible only to the logged-in user. `BW_PASSWORD` in `.env` is a plaintext file on disk.

**Linux/Windows alternative:** Use `--passwordfile` instead:
```bash
echo "master_password" > ~/.bw_master_pass  # chmod 600 immediately
chmod 600 ~/.bw_master_pass
bw unlock --passwordfile ~/.bw_master_pass --raw
```

## Session Key Management

Since each Hermes `terminal()` call starts a fresh shell, `BW_SESSION` does not persist. Pattern for vault-data commands:

```bash
# Option A: Inline --session flag (most explicit)
SESSION_KEY=$(bw unlock --passwordenv BW_PASSWORD --raw)
bw get password GitHub --session "$SESSION_KEY"

# Option B: Export in the same call
export BW_SESSION="$(bw unlock --passwordenv BW_PASSWORD --raw)" && bw list items

# Option C: For interactive unlock (master password prompt), use PTY
# terminal(command="bw unlock", pty=true, background=true)
# Then copy the BW_SESSION export line from output
```

## Creating a Login Item (jq + encode pipeline)

**Never nest `jq` inside `jq`** — command substitution inside a jq program
fails with a syntax error (and can crash the CLI with EPIPE). Save the
template to a file first:

```bash
# 1. Save template
bw get template item > /tmp/bw-item.json

# 2. jq the FILE (not a pipe from another jq)
jq --arg pw "$(bw generate -ulns --length 25)" \
   '.name = "Service Name"
    | .login.username = "user@example.com"
    | .login.password = $pw
    | .login.uris = [{"uri": "https://service.example.com", "match": 3}]' \
   /tmp/bw-item.json | bw encode | bw create item
```

`match` values: 0=Domain, 1=Host, 2=StartsWith, 3=Exact, 4=Regex, 5=None.

**`.login.uris` must be an array** — a `.login.uri` string assignment is
silently dropped by the server (the item is created with no URI; verified:
`bw get uri <name>` returns "Not found").

## Creating a Secure Note

```bash
bw get template item > /tmp/bw-item.json
jq '.name = "My Secure Note"
    | .type = 2
    | .secureNote.type = 0
    | .notes = "Contents of my secure note."' \
   /tmp/bw-item.json | bw encode | bw create item
```

## Editing an Item (read-modify-write)

```bash
# Update the password
bw get item ITEM_ID > /tmp/bw-item.json
jq --arg pw "$(bw generate -ulns --length 25)" '.login.password = $pw' /tmp/bw-item.json | bw encode | bw edit item ITEM_ID

# Add a custom field
bw get item ITEM_ID | jq '.fields += [{"name":"api_key","value":"secret123","type":0}]' | bw encode | bw edit item ITEM_ID

# Update collection membership (org items)
echo '["collection-id-1","collection-id-2"]' | bw encode | bw edit item-collections ITEM_ID --organizationid ORG_ID
```

## Searching and Getting Items

```bash
# Search and list results as a table
bw list items --search "github" --pretty | jq -r '.[] | "\(.id)\t\(.name)\t\(.login.username // "")"'

# Get password by search term (raw output)
bw get password "GitHub" --raw

# Get TOTP code (rotates every 30 seconds)
bw get totp "GitHub" --raw

# Get full item by exact ID
bw get item abc123-def456-... --pretty

# Get item ID from search term (for use in edits)
bw get item "GitHub" --raw | jq -r '.id'
```

## Item Creation with Full Template (All Fields)

```bash
# Login item with all common fields
bw get template item | jq '
  .name = "Production API" |
  .notes = "API credentials for prod" |
  .login.username = "api-user" |
  .login.password = "generated-password" |
  .login.uris = [{"uri":"https://api.example.com","match":3}] |
  .fields = [
    {"name":"region","value":"us-east-1","type":0},
    {"name":"active","value":"true","type":2}
  ]
' | bw encode | bw create item
```

## Send Workflows

```bash
# Text send (hidden) — quick flag form (recommended; computes deletionDate)
bw send -n "Deploy Key" -d 3 --hidden "ssh-rsa AAAA..."

# File send (7 days)
bw send -n "Config" -f ./config.json -d 7

# Send with password protection
bw send -n "Secret" -d 7 --hidden "supersecret" --password "access-code-123"

# Receive a send
bw receive "https://vault.bitwarden.net/#/send/..." --raw

# Receive with password
bw receive "https://vault.bitwarden.net/#/send/..." --password "access-code-123" --output ./downloaded_file
```

### Send subcommands (template-based create)

`bw list send` is **invalid** — use `bw send list`:

```bash
bw send list                          # list your Sends
bw send template text                 # JSON template (also: file)
bw send get <send-id>
bw send delete <send-id>
bw send remove-password <send-id>
```

**`bw send create` requires a valid `deletionDate`** — the template ships
`deletionDate: null`, which fails with "Must specify a valid deletion date
after the current time". Set a future ISO-8601 timestamp, or use the quick
flag form (`-d <days>`) which computes it for you:

```bash
bw send template text | jq --arg del "$(date -u -v+7d +%Y-%m-%dT%H:%M:%S.000Z)" \
  '.name="Key" | .text="secret" | .deletionDate=$del | .notes=null' \
  | bw encode | bw send create
```

## Export/Import

```bash
# Export entire vault as JSON — PLAINTEXT! ("encrypted": false in header)
bw export --format json --output ./vault.json
chmod 600 ./vault.json   # treat as a secret; delete after use

# Encrypted export (password-protected)
bw export --format encrypted_json --password "export-pw" --output ./vault.json

# Export a specific organization's vault
bw export --organizationid ORG_ID --format csv --output ./org_vault.csv

# Import from another password manager
bw import lastpasscsv ./lastpass_export.csv

# List supported import formats
bw import --formats
```

## Password Generation

```bash
# Default: 14-char (lowercase, uppercase, numbers)
bw generate

# Complex: 25 chars with special chars
bw generate -ulns --length 25

# No ambiguous characters
bw generate --ambiguous

# Passphrase (3 words, dash separator)
bw generate --passphrase

# Custom passphrase
bw generate -p --words 5 --separator "_" --capitalize
```

## Organization Workflows

```bash
# List organizations you belong to
bw list organizations --pretty

# List collections in an org
bw list org-collections --organizationid ORG_ID --pretty

# List members in an org
bw list org-members --organizationid ORG_ID --pretty

# Move an item to an org (requires collection encoding)
echo '["collection-uuid-1"]' | bw encode | bw move ITEM_ID ORG_ID

# Confirm an invited org member (admin only)
bw confirm org-member MEMBER_ID --organizationid ORG_ID
```

## Bulk Operations

```bash
# Find weak passwords (report command does not exist in v2026.7.0 —
# export + jq is the way)
bw export --format json --output /tmp/vault.json && chmod 600 /tmp/vault.json
jq '.[] | select(.login) | {name: .name, len: (.login.password | length // 0)} | select(.len < 12)' /tmp/vault.json
rm -f /tmp/vault.json
```


## Keychain integration (macOS)

> See `references/keychain.md` for the full Keychain service naming
> convention, one-time setup, and retrieval patterns.

The `scripts/bw-unlock.sh` helper automatically retrieves `BW_PASSWORD` from
Apple Keychain via `security find-generic-password -s "Bitwarden-Master" -w`
when the env var is unset — Keychain is the standard credential source, and
`.env` is a non-macOS fallback only.
