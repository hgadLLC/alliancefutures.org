// Eleventy config. During the migration, Eleventy reads markdown content from
// content/ and emits HTML into _site/. The existing hand-built HTML files at
// the repo root remain authoritative for now — Eleventy output won't replace
// the live site until Phase 4 (the GitHub Pages cutover).
//
// See admin/MIGRATION-PLAN.md for the staged rollout.

const yaml = require("js-yaml");

module.exports = function (eleventyConfig) {
    // Treat .yml files in _data/ as Eleventy data files.
    eleventyConfig.addDataExtension("yml", (contents) => yaml.load(contents));

    // Static assets passthrough — Eleventy copies them into _site/ unchanged.
    eleventyConfig.addPassthroughCopy("css");
    eleventyConfig.addPassthroughCopy("images");
    eleventyConfig.addPassthroughCopy("favicon.ico");
    eleventyConfig.addPassthroughCopy({ "embassy-monitors/pdfs": "embassy-monitors/pdfs" });
    eleventyConfig.addPassthroughCopy({ "embassy-monitors/images": "embassy-monitors/images" });
    eleventyConfig.addPassthroughCopy({ "publications/images": "publications/images" });
    eleventyConfig.addPassthroughCopy({ "our-work/commentary/images": "our-work/commentary/images" });
    eleventyConfig.addPassthroughCopy({ "our-work/commentary/*.pdf": "our-work/commentary/" });

    // Static pages that aren't CMS-managed — copy from the repo root as-is.
    // These ship verbatim until/unless they get migrated into content/pages/.
    for (const file of ["about.html", "advisory.html", "support.html", "privacy.html"]) {
        eleventyConfig.addPassthroughCopy(file);
    }
    // Listing pages that aren't yet rebuilt from data — passthrough until they
    // become Eleventy-driven in a follow-up phase.
    eleventyConfig.addPassthroughCopy({ "people.html": "people.html" });
    eleventyConfig.addPassthroughCopy({ "embassy-monitors/index.html": "embassy-monitors/index.html" });
    eleventyConfig.addPassthroughCopy({ "our-work/index.html": "our-work/index.html" });
    eleventyConfig.addPassthroughCopy({ "our-work/research.html": "our-work/research.html" });
    eleventyConfig.addPassthroughCopy({ "our-work/futures.html": "our-work/futures.html" });
    eleventyConfig.addPassthroughCopy({ "our-work/commentary.html": "our-work/commentary.html" });
    eleventyConfig.addPassthroughCopy({ "publications/index.html": "publications/index.html" });
    // The homepage is also passthrough for now — it has hand-written hero copy
    // that needs structured frontmatter before the CMS can edit it cleanly.
    eleventyConfig.addPassthroughCopy({ "index.html": "index.html" });

    // Markdown rendering filter for prose blocks stored in frontmatter
    // (summary, theme bodies, ambassador's corner, etc.).
    const MarkdownIt = require("markdown-it");
    const md = new MarkdownIt({ html: true, linkify: false, typographer: false });
    const calloutMd = new MarkdownIt({ html: true, linkify: false, typographer: false })
        .use((md) => {
            // For callout boxes we want each paragraph to carry the callout class.
            md.renderer.rules.paragraph_open = () => '<p class="callout-box__text">';
        });
    eleventyConfig.addFilter("markdownify", (str, opts) => {
        if (!str) return "";
        if (opts && opts.callout) return calloutMd.render(String(str));
        return md.render(String(str));
    });

    // Custom filters used by templates. Dates are formatted in UTC so a YYYY-MM-DD
    // frontmatter value never shifts under the build machine's local timezone.
    const MONTHS_LONG = ["January","February","March","April","May","June","July","August","September","October","November","December"];
    const MONTHS_SHORT = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
    const ymd = (iso) => {
        if (iso instanceof Date) {
            return [iso.getUTCFullYear(), iso.getUTCMonth(), iso.getUTCDate()];
        }
        const m = String(iso).match(/^(\d{4})-(\d{2})-(\d{2})/);
        if (!m) return null;
        return [parseInt(m[1], 10), parseInt(m[2], 10) - 1, parseInt(m[3], 10)];
    };
    eleventyConfig.addFilter("dateShort", (iso) => {
        const p = ymd(iso); if (!p) return "";
        return `${MONTHS_SHORT[p[1]]} ${p[2]}, ${p[0]}`;
    });
    eleventyConfig.addFilter("dateLong", (iso) => {
        const p = ymd(iso); if (!p) return "";
        return `${MONTHS_LONG[p[1]]} ${p[2]}, ${p[0]}`;
    });

    // Recent Work composition for bio pages. Combines external mentions and
    // internal publications for a given person slug, sorted newest first.
    const TYPE_LABELS = {
        monitor: "Embassies Monitor",
        report: "Report",
        redteam: "Red Team Report",
        brief: "Brief",
        commentary: "Commentary",
        "op-ed": "Op-Ed",
        media: "In the Media",
        interview: "Interview",
        podcast: "Podcast",
        panel: "Panel",
        citation: "Citation",
        book: "Book / Edited Volume",
        chapter: "Book Chapter",
    };
    const MAX_RECENT = 12;
    const toIsoString = (d) => {
        if (!d) return "";
        if (d instanceof Date) return d.toISOString().slice(0, 10);
        return String(d);
    };
    const dateDisplay = (iso) => {
        const p = ymd(iso); if (!p) return "";
        return `${MONTHS_SHORT[p[1]]} ${p[2]}, ${p[0]}`;
    };
    const normalizeInternalUrl = (url) => {
        if (!url) return "#";
        if (/^(https?:)?\/\//.test(url)) return url;
        return url.startsWith("/") ? url : "/" + url;
    };
    eleventyConfig.addFilter("recentWorkFor", function (slug) {
        const mentions = this.ctx.mentions || this.ctx.collections?.all?.find?.(() => false) || [];
        const internalPubs = this.ctx.internalPublications || [];
        const items = [];
        for (const m of mentions) {
            if (m.author === slug) {
                items.push({ ...m, internal: false, _date: toIsoString(m.date) });
            }
        }
        for (const pub of internalPubs) {
            if (Array.isArray(pub.authors) && pub.authors.includes(slug)) {
                items.push({ ...pub, internal: true, _date: toIsoString(pub.date) });
            }
        }
        items.sort((a, b) => (b._date || "").localeCompare(a._date || ""));
        return items.slice(0, MAX_RECENT).map((item) => ({
            url: item.internal ? normalizeInternalUrl(item.url) : item.url,
            external: !item.internal,
            type_label: TYPE_LABELS[item.type] || (item.type || "").replace(/\b\w/g, (c) => c.toUpperCase()),
            title: item.title || "",
            outlet: item.outlet || "",
            excerpt: item.excerpt || "",
            date_display: dateDisplay(item._date),
        }));
    });

    return {
        dir: {
            input: "content",
            includes: "../_includes",
            data: "../_data",
            output: "_site",
        },
        templateFormats: ["md", "njk", "html"],
        markdownTemplateEngine: "njk",
        htmlTemplateEngine: "njk",
        dataTemplateEngine: "njk",
    };
};
