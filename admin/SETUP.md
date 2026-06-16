# /admin/ — one-time setup

The TAFI admin lives at **https://alliancefutures.org/admin/**. It's a static
single-page app ([Sveltia CMS](https://github.com/sveltia/sveltia-cms)) that
lets editors update the site by filling in forms. Submissions land as commits
to the GitHub repo, and GitHub Pages rebuilds the live site.

**Auth is GitHub.** Editors sign in with a GitHub account; submissions are
attributed to that account. There's no Netlify, no Identity service, no
OAuth proxy of our own — Sveltia bundles its own hosted OAuth bridge at
auth.sveltia.app.

(Earlier iterations of this file pointed at Netlify Identity + Git Gateway.
That path was abandoned because Netlify's Identity API is partially
undocumented and the dashboard setup is fragile. The Sveltia route works
end-to-end without any third-party dashboard work.)

---

## To grant yourself access

The repo owner already has access — just go to
https://alliancefutures.org/admin/, click **"Sign in with GitHub"**,
authorise the Sveltia auth bridge on first use, and you're in.

---

## To add another editor

1. Go to https://github.com/hgadLLC/alliancefutures.org/settings/access
2. Click **"Add people"** and enter the editor's GitHub username
3. Pick the **Write** role (or **Maintain** if you want them to be able to
   change branch protections too)
4. Send the invite
5. Tell them to accept the invite, then go to
   https://alliancefutures.org/admin/ and sign in with GitHub

No password reset flow, no email/password user db to maintain. If you need to
revoke an editor's access, remove them from the repo's collaborators list.

---

## Updating the CMS script (rare)

`admin/index.html` pins Sveltia CMS by exact version + SRI hash. To bump:

```bash
VER=0.170.0  # or whatever
URL="https://unpkg.com/@sveltia/cms@${VER}/dist/sveltia-cms.js"
curl -sL "$URL" -o /tmp/sveltia.js
openssl dgst -sha384 -binary /tmp/sveltia.js | openssl base64 -A
```

Update both the URL and the `integrity="sha384-..."` attribute in
`admin/index.html`. The SRI hash protects against a compromised CDN serving
altered admin JavaScript — don't drop it.

---

## Cleaning up after the Netlify detour

If you created a Netlify site during the earlier setup attempt, you can
safely delete it:

1. https://app.netlify.com → click into `tafi-admin` (or whatever you named it)
2. **Site settings → Danger zone → Delete this site**

Then revoke any lingering tokens at
https://app.netlify.com/user/applications and https://github.com/settings/tokens.

---

## What's next

- **Phase 2 (next):** Migrate all 18 monitor issues, 3 commentaries, 2 red-team
  reports, 9 bios, and the homepage to markdown files under `content/`. Verify
  Eleventy build output matches the current site. Live deploy untouched.
- **Phase 3:** Expand `admin/config.yml` to cover special reports, commentary,
  red-team reports, homepage hero, channel cards, support page, etc.
- **Phase 4:** Cut over GitHub Pages source from `main` to `gh-pages` (the
  Eleventy build output). Live site begins serving CMS-authored content.

Until Phase 4 cuts over, edits made in the CMS will land as commits but
won't yet be visible on the public site because GitHub Pages is still serving
the hand-built HTML from `main`. The migration plan (in
`admin/MIGRATION-PLAN.md`) details the cutover safely.
