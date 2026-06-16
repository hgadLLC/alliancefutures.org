# /admin/ — one-time setup

The TAFI admin lives at **https://alliancefutures.org/admin/**. It's a static
single-page app (Decap CMS) that lets non-technical editors update the site by
filling in forms. Submissions land as commits to the GitHub repo, and GitHub
Pages rebuilds the live site.

Auth is **email/password via Netlify Identity**. Editors don't need a GitHub
account; they just need an invite email.

Phase 1 (the scaffold) is in. To turn the admin from "loads but rejects logins"
into "fully working," do these one-time steps **once**.

---

## 1. Create the Netlify "phantom" site

Netlify hosts the Identity service + Git Gateway proxy. The site files
themselves keep deploying from GitHub Pages — Netlify never serves the public
pages.

1. Go to https://app.netlify.com and sign up (free tier).
2. Click **Add new site → Import an existing project**.
3. Choose **Deploy with GitHub**, authorise Netlify on the
   `hgadLLC/alliancefutures.org` repo.
4. On the build settings step:
   - **Branch to deploy:** `main`
   - **Build command:** leave empty (we don't deploy this site from Netlify)
   - **Publish directory:** leave empty
   - Click **Deploy site**.
5. After the initial (no-op) deploy finishes, go to **Site settings →
   General → Site information**. Rename the site to something obvious like
   `tafi-admin`. Your Netlify URL is now `https://tafi-admin.netlify.app`.

---

## 2. Enable Identity

1. In the new Netlify site dashboard, open **Identity** (sidebar) and click
   **Enable Identity**.
2. Under **Identity → Registration**, set **Registration preferences** to
   **Invite only**. (No one self-signs-up.)
3. Under **Identity → External providers**, leave everything off (we're using
   email/password).
4. Under **Identity → Emails**, customise the invite email template if you
   want (optional).

---

## 3. Enable Git Gateway

1. In the Netlify site dashboard, go to **Identity → Services → Git Gateway**.
2. Click **Enable Git Gateway**. Netlify will OAuth into GitHub and ask for
   permission to push to the `hgadLLC/alliancefutures.org` repo. Grant it.
3. Git Gateway is now active. The CMS will use this proxy to commit edits.

---

## 4. Point the admin page at your Netlify site

The admin page needs to know which Netlify project owns Identity. By default
the widget tries to auto-detect via the current domain; on a custom domain
(alliancefutures.org) we need to set the API URL explicitly.

After step 1 you'll have a Netlify URL like `https://tafi-admin.netlify.app`.
Either:

**Option A — add the meta tag (simpler).** In `/admin/index.html`, just before
the closing `</head>`, add:

```html
<meta name="netlify-identity-api-url" content="https://tafi-admin.netlify.app/.netlify/identity">
```

(Use your actual Netlify URL.) Commit and push.

**Option B — initialise the widget in JS.** Replace the existing init block
at the bottom of `/admin/index.html` with:

```js
if (window.netlifyIdentity) {
    window.netlifyIdentity.init({
        APIUrl: "https://tafi-admin.netlify.app/.netlify/identity"
    });
}
```

Either works; A is one less line.

---

## 5. Invite yourself

1. In Netlify → **Identity → Users**, click **Invite users**.
2. Enter your email. Netlify sends an invitation.
3. Open the invite email, click the **Accept the invite** link. It will bounce
   you to `https://alliancefutures.org/admin/#invite_token=...`. The widget
   picks up the token, asks you to set a password, then logs you in to the
   CMS.
4. Repeat for every editor you want to give access. They don't need to be on
   GitHub.

---

## 6. Smoke test

1. After accepting your invite, you should see the CMS interface with one
   tab visible ("Embassies Monitor") and another ("People"). They'll be empty
   until Phase 2 migration is done.
2. Click **Embassies Monitor → New Monitor issue**, fill in a few fields,
   hit **Publish**. Within a few seconds a new commit `CMS: add monitors
   'week-99'` should appear in the GitHub repo.
3. **Delete that test commit** (it has no template yet to render against).
   You've now verified the round trip works.

---

## Updating CMS scripts (rare)

`admin/index.html` pins Decap CMS and Netlify Identity widget by version +
SRI hash. If you want to bump either to a newer version:

```bash
# 1. Pick the new version, e.g. decap-cms@3.6.0
curl -sL "https://unpkg.com/decap-cms@3.6.0/dist/decap-cms.js" -o /tmp/decap.js
openssl dgst -sha384 -binary /tmp/decap.js | openssl base64 -A
# 2. Update both the URL and the integrity="sha384-..." attribute in admin/index.html
```

The SRI hash protects against a compromised CDN serving altered JavaScript.
Don't drop it.

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
