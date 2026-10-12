<!-- Deprecated: enum tables merged into references/cli-commands.md in the canonical in-repo skill. -->

# BitWarden CLI Enum Values

## Two-Step Login Methods

Used with `bw login --method <value>`:

| Name | Value |
|---|---|
| Authenticator | 0 |
| Email | 1 |
| YubiKey | 3 |

> **Note:** FIDO2 and Duo are NOT supported by the CLI. If your account uses these, use API key login (`bw login --apikey`) instead.

## Item Types

Used in the `create`/`edit` workflow with `.type` field:

| Name | Value |
|---|---|
| Login | 1 |
| Secure Note | 2 |
| Card | 3 |
| Identity | 4 |
| SSH Key | 5 |

Secure Notes require a sub-template: `.secureNote.type` (0 = general, 1 = login, 2 = windows, 3 = mac, 4 = linux, 5 = bank).

## Login URI Match Types

Used with create/edit to set `.login.uri` match detection:

| Name | Value |
|---|---|
| Domain | 0 |
| Host | 1 |
| Starts With | 2 |
| Exact | 3 |
| Regular Expression | 4 |
| Never | 5 |

## Custom Field Types

Used in `.fields[]` array:

| Name | Value |
|---|---|
| Text | 0 |
| Hidden | 1 |
| Boolean | 2 |

## Organization User Types

| Name | Value |
|---|---|
| Owner | 0 |
| Admin | 1 |
| User | 2 |
| Manager | 3 |
| Custom | 4 |

## Organization User Statuses

| Name | Value |
|---|---|
| Invited | 0 |
| Accepted | 1 |
| Confirmed | 2 |
| Revoked | -1 |

## `bw list` Object Types

- `items` — all vault items
- `folders` — all folders
- `collections` — all collections (agnostic of org)
- `org-collections` — collections for a specific org (`--organizationid`)
- `organizations` — orgs you belong to
- `org-members` — members of a specific org (`--organizationid`)

## `bw get` Object Types

- `item` — full item JSON (by ID or search term)
- `username` — username field only
- `password` — password field only (raw with `--raw`)
- `uri` — first URI
- `totp` — current TOTP code
- `notes` — notes field
- `exposed` — check if password found in a breach
- `attachment` — download a file attachment (`--itemid`, `--output`)
- `folder`, `collection`, `org-collection` — by ID or search term
- `organization` — org details
- `template` — JSON template for create/edit workflows
- `fingerprint` — user's fingerprint phrase (use `me` for your own)
- `send` — Bitwarden Send object by ID

## `bw export` Formats

- `csv` (default)
- `json`
- `encrypted_json` (with `--password`)
- `zip` (includes attachments)

## Supported 2FA / Two-Step Login Methods Summary

| Method | CLI Support | Notes |
|---|---|---|
| Authenticator app (TOTP) | ✅ | method=0 |
| Email code | ✅ | method=1 |
| YubiKey | ✅ | method=3 |
| FIDO2 | ❌ | Use `--apikey` login instead |
| Duo | ❌ | Use `--apikey` login instead |
