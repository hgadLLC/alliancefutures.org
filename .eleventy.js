// Eleventy config. During the migration, Eleventy reads markdown content from
// content/ and emits HTML into _site/. The existing hand-built HTML files at
// the repo root remain authoritative for now — Eleventy output won't replace
// the live site until Phase 4 (the GitHub Pages cutover).
//
// See admin/MIGRATION-PLAN.md for the staged rollout.

module.exports = function (eleventyConfig) {
    // Static assets passthrough — Eleventy copies them into _site/ unchanged.
    eleventyConfig.addPassthroughCopy("css");
    eleventyConfig.addPassthroughCopy("images");
    eleventyConfig.addPassthroughCopy("favicon.ico");
    eleventyConfig.addPassthroughCopy("admin");
    eleventyConfig.addPassthroughCopy({ "embassy-monitors/pdfs": "embassy-monitors/pdfs" });
    eleventyConfig.addPassthroughCopy({ "embassy-monitors/images": "embassy-monitors/images" });
    eleventyConfig.addPassthroughCopy({ "publications/images": "publications/images" });
    eleventyConfig.addPassthroughCopy({ "our-work/commentary/images": "our-work/commentary/images" });
    eleventyConfig.addPassthroughCopy({ "our-work/commentary/*.pdf": "our-work/commentary/" });

    // Custom filters used by templates.
    eleventyConfig.addFilter("dateShort", (iso) => {
        const d = typeof iso === "string" ? new Date(iso + "T00:00:00") : new Date(iso);
        return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
    });
    eleventyConfig.addFilter("dateLong", (iso) => {
        const d = typeof iso === "string" ? new Date(iso + "T00:00:00") : new Date(iso);
        return d.toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" });
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
