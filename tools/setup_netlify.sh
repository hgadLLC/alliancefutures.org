#!/usr/bin/env bash
# tools/setup_netlify.sh — one-time Netlify Identity + Git Gateway setup
#
# Sets up the Netlify "phantom" project that powers /admin/ on
# alliancefutures.org. Run once locally with two short-lived tokens, then
# revoke both immediately.
#
# Usage:
#   NETLIFY_TOKEN=nfp_xxx GITHUB_TOKEN=ghp_xxx bash tools/setup_netlify.sh
#
# After it finishes you'll get an invite email from Netlify. Click "Accept
# invite", set a password, then log in to https://alliancefutures.org/admin/.
#
# Then revoke both tokens (one-click each):
#   Netlify: https://app.netlify.com/user/applications
#   GitHub:  https://github.com/settings/tokens

set -euo pipefail

REPO="hgadLLC/alliancefutures.org"
SITE_NAME="${TAFI_SITE_NAME:-tafi-admin}"

# ----- Token checks ---------------------------------------------------------
if [[ -z "${NETLIFY_TOKEN:-}" ]]; then
    echo "Error: NETLIFY_TOKEN env var not set." >&2
    echo "Get one at https://app.netlify.com/user/applications#personal-access-tokens" >&2
    exit 1
fi
if [[ -z "${GITHUB_TOKEN:-}" ]]; then
    echo "Error: GITHUB_TOKEN env var not set." >&2
    echo "Create a PAT (classic) with 'repo' scope at https://github.com/settings/tokens" >&2
    exit 1
fi

# ----- Helpers --------------------------------------------------------------
nl() {  # curl wrapper that talks to the Netlify API
    curl -sS \
         -H "Authorization: Bearer ${NETLIFY_TOKEN}" \
         -H "Content-Type: application/json" \
         "$@"
}

json_field() {  # extract a top-level JSON field via python3
    python3 -c "import sys, json
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
print(d.get('$1', '') if isinstance(d, dict) else '')"
}

# ----- 1) Verify tokens -----------------------------------------------------
echo "→ Verifying Netlify token…"
NL_USER=$(nl https://api.netlify.com/api/v1/user)
NL_EMAIL=$(echo "$NL_USER" | json_field email)
NL_NAME=$(echo "$NL_USER" | json_field full_name)
if [[ -z "$NL_EMAIL" ]]; then
    echo "  Netlify token rejected. Response:" >&2
    echo "$NL_USER" >&2
    exit 1
fi
echo "  Netlify user: ${NL_NAME:-(no name set)} <$NL_EMAIL>"

echo "→ Verifying GitHub token…"
GH_USER=$(curl -sS -H "Authorization: token ${GITHUB_TOKEN}" https://api.github.com/user)
GH_LOGIN=$(echo "$GH_USER" | json_field login)
if [[ -z "$GH_LOGIN" ]]; then
    echo "  GitHub token rejected. Response:" >&2
    echo "$GH_USER" >&2
    exit 1
fi
echo "  GitHub user: $GH_LOGIN"

# ----- 2) Find or create the Netlify site -----------------------------------
echo "→ Looking for existing Netlify site named '$SITE_NAME'…"
SITES=$(nl "https://api.netlify.com/api/v1/sites?name=$SITE_NAME")
SITE_ID=$(echo "$SITES" | python3 -c "
import sys, json
sites = json.load(sys.stdin)
if isinstance(sites, list):
    for s in sites:
        if s.get('name') == '$SITE_NAME':
            print(s.get('id', ''))
            break
")

if [[ -z "$SITE_ID" ]]; then
    echo "  Not found — creating it…"
    NEW_SITE=$(nl -X POST -d "{\"name\":\"$SITE_NAME\"}" \
                  https://api.netlify.com/api/v1/sites)
    SITE_ID=$(echo "$NEW_SITE" | json_field id)
    if [[ -z "$SITE_ID" ]]; then
        echo "  Error creating site:" >&2
        echo "$NEW_SITE" >&2
        exit 1
    fi
    echo "  Created site $SITE_ID"
else
    echo "  Found existing site $SITE_ID"
fi

SITE=$(nl "https://api.netlify.com/api/v1/sites/$SITE_ID")
SITE_URL=$(echo "$SITE" | json_field url)
SITE_SSL_URL=$(echo "$SITE" | json_field ssl_url)
[[ -n "$SITE_SSL_URL" ]] && SITE_URL="$SITE_SSL_URL"
IDENTITY_API_URL="$SITE_URL/.netlify/identity"
echo "  Site URL:         $SITE_URL"
echo "  Identity API URL: $IDENTITY_API_URL"

# ----- 3) Enable Identity ---------------------------------------------------
echo "→ Enabling Identity…"
IDENTITY_RESP=$(nl -X POST "https://api.netlify.com/api/v1/sites/$SITE_ID/identity" 2>&1 || true)
if echo "$IDENTITY_RESP" | grep -qiE "already|enabled"; then
    echo "  Already enabled."
elif echo "$IDENTITY_RESP" | grep -qi "error"; then
    echo "  ! API returned an error. Enable manually:"
    echo "      Netlify dashboard → this site → Identity → Enable Identity"
    echo "    Response was: $IDENTITY_RESP"
else
    echo "  Enabled."
fi
sleep 3

# ----- 4) Set Identity to invite-only ---------------------------------------
echo "→ Setting Identity to invite-only…"
SETTINGS_RESP=$(nl -X PUT \
    -d '{"disable_signup": true, "autoconfirm": false}' \
    "https://api.netlify.com/api/v1/sites/$SITE_ID/identity" 2>&1 || true)
if echo "$SETTINGS_RESP" | grep -qiE "error|not found"; then
    echo "  ! Couldn't set via API. In dashboard:"
    echo "      Identity → Registration → set to 'Invite only'"
else
    echo "  Set."
fi

# ----- 5) Enable Git Gateway ------------------------------------------------
echo "→ Enabling Git Gateway with $REPO …"
GG_RESP=$(nl -X POST \
    -d "{\"github\":{\"repo\":\"$REPO\",\"api_token\":\"$GITHUB_TOKEN\"}}" \
    "https://api.netlify.com/api/v1/sites/$SITE_ID/services/git/instances" 2>&1 || true)
if echo "$GG_RESP" | grep -qiE "error|denied|not authorized"; then
    echo "  ! API attempt didn't go through. Enable manually:"
    echo "      Identity → Services → Git Gateway → Enable"
    echo "      (When it prompts for GitHub OAuth, authorise it on $REPO.)"
    echo "    API response was: $GG_RESP"
else
    echo "  Enabled."
fi

# ----- 6) Patch admin/index.html --------------------------------------------
echo "→ Patching admin/index.html with the Identity API URL…"
if grep -q 'netlify-identity-api-url' admin/index.html; then
    echo "  Already patched."
else
    python3 - "$IDENTITY_API_URL" <<'PY'
import sys
url = sys.argv[1]
path = "admin/index.html"
content = open(path).read()
tag = f'    <meta name="netlify-identity-api-url" content="{url}">\n'
if "netlify-identity-api-url" not in content:
    content = content.replace("</title>\n", "</title>\n" + tag, 1)
    open(path, "w").write(content)
    print("  Inserted meta tag.")
else:
    print("  Already present.")
PY
fi

# ----- 7) Invite the project owner ------------------------------------------
echo "→ Inviting $NL_EMAIL to Identity…"
INVITE_RESP=$(nl -X POST -d "{\"email\":\"$NL_EMAIL\"}" \
    "https://api.netlify.com/api/v1/sites/$SITE_ID/identity/users" 2>&1 || true)
if echo "$INVITE_RESP" | grep -qiE "exists|already"; then
    echo "  User already exists. Skipping (you can log in directly)."
elif echo "$INVITE_RESP" | grep -qi "error"; then
    echo "  ! Couldn't invite via API. In the dashboard:"
    echo "      Identity → Users → Invite users → enter $NL_EMAIL"
    echo "    API response was: $INVITE_RESP"
else
    echo "  Invite email sent to $NL_EMAIL."
fi

# ----- 8) Wrap up -----------------------------------------------------------
cat <<EOF

=========================================================
 DONE. Next steps:
=========================================================

  1. Check your inbox at $NL_EMAIL for the Netlify invite.
  2. Click "Accept invite", set a password — you'll land in /admin/.
  3. Commit the admin/index.html patch:

         git add admin/index.html
         git commit -m "Wire admin to Netlify Identity"
         git push

  4. Revoke both tokens NOW (one click each):

         Netlify: https://app.netlify.com/user/applications
         GitHub:  https://github.com/settings/tokens

  The Netlify-side "phantom" project is now live and authoring through
  /admin/ will land as commits to this repo. Phase 2 (content migration)
  comes next; until that's done the CMS works but has nothing to edit.

EOF
