#!/usr/bin/env python3
"""Generator for TAFI team bio pages.

This script:
  1. Renders bio HTML from the PEOPLE list below.
  2. Reads data/mentions.yml (external mentions) and
     data/internal-publications.yml (TAFI's own work).
  3. Merges them per author and emits a "Recent Work"
     section at the bottom of each bio.

To regenerate after editing the YAML files, run from project root:
  python3 team/_build_bios.py
"""
import datetime
import pathlib
import yaml

OUT = pathlib.Path(__file__).resolve().parent
ROOT = OUT.parent

MAX_RECENT_ITEMS = 12
ITEMS_VISIBLE_BEFORE_COLLAPSE = 5

TYPE_LABELS = {
    "monitor": "Embassies Monitor",
    "report": "Report",
    "redteam": "Red Team Report",
    "brief": "Brief",
    "commentary": "Commentary",
    "op-ed": "Op-Ed",
    "media": "In the Media",
    "interview": "Interview",
    "podcast": "Podcast",
    "panel": "Panel",
    "citation": "Citation",
    "book": "Book / Edited Volume",
    "chapter": "Book Chapter",
}


def load_yaml(path):
    p = ROOT / path
    if not p.exists():
        return []
    return yaml.safe_load(p.read_text()) or []


def load_recent_work():
    """Return {slug: [item, ...]} sorted newest first, capped at MAX_RECENT_ITEMS."""
    by_author = {}

    # External mentions: each item has a single `author`
    for m in load_yaml("data/mentions.yml"):
        author = m.get("author")
        if not author:
            continue
        item = {**m, "internal": False}
        by_author.setdefault(author, []).append(item)

    # Internal publications: each item has an `authors` list
    for pub in load_yaml("data/internal-publications.yml"):
        for slug in pub.get("authors", []) or []:
            item = {**pub, "author": slug, "internal": True}
            by_author.setdefault(slug, []).append(item)

    # Sort by date descending, cap.
    for slug, items in by_author.items():
        items.sort(key=lambda x: str(x.get("date", "")), reverse=True)
        by_author[slug] = items[:MAX_RECENT_ITEMS]
    return by_author


def render_recent_item(item, hidden=False):
    """One row in the Recent Work list."""
    type_label = TYPE_LABELS.get(item.get("type"), item.get("type", "").title())
    outlet = item.get("outlet", "")
    title = item.get("title", "")
    url = item.get("url", "#")
    if item.get("internal"):
        # Internal pages are project-root-relative; bio sits at /team/, so prepend ../
        if not url.startswith(("http://", "https://", "..", "/")):
            url = f"../{url}"
    raw_date = item.get("date")
    if isinstance(raw_date, (datetime.date, datetime.datetime)):
        date_str = raw_date.strftime("%b %-d, %Y")
    else:
        date_str = str(raw_date) if raw_date else ""
    excerpt = item.get("excerpt", "")
    excerpt_html = f'<p class="rw-excerpt">{excerpt}</p>' if excerpt else ""

    target = ' target="_blank" rel="noopener"' if str(url).startswith(("http://", "https://")) else ""
    cls = "rw-item rw-hidden" if hidden else "rw-item"
    return f"""                    <a href="{url}" class="{cls}"{target}>
                        <div class="rw-meta">
                            <span class="rw-type">{type_label}</span>
                            <span class="rw-date">{date_str}</span>
                        </div>
                        <div class="rw-body">
                            <h4 class="rw-title">{title}</h4>
                            <p class="rw-outlet">{outlet}</p>
                            {excerpt_html}
                        </div>
                    </a>"""


def render_recent_work_section(slug, items):
    if not items:
        return ""
    rows = []
    for i, it in enumerate(items):
        rows.append(render_recent_item(it, hidden=(i >= ITEMS_VISIBLE_BEFORE_COLLAPSE)))
    rows_html = "\n".join(rows)
    extra = len(items) - ITEMS_VISIBLE_BEFORE_COLLAPSE
    toggle_html = ""
    if extra > 0:
        toggle_html = f"""
                <button type="button" class="rw-toggle" aria-expanded="false">
                    <span class="rw-toggle-more">Show {extra} more</span>
                    <span class="rw-toggle-less">Show fewer</span>
                </button>"""
    return f"""                <h2>Recent Work</h2>
                <div class="recent-work-list">
{rows_html}
                </div>{toggle_html}"""

PEOPLE = [
    {
        "slug": "greg-brown",
        "name": "Dr. Greg Brown",
        "title": "Founding & Executive Director",
        "photo": "greg-brown.webp",
        "email": "gbrown@alliancefutures.org",
        "linkedin": "https://www.linkedin.com/in/gregoryessbrown/",
        "prev": None,
        "next": ("eric-lies", "Eric Lies"),
        "hero_lede": "Leads TAFI's research on how alliances form, fracture, and adapt &mdash; with a focus on the Indo-Pacific, where partnership architectures are shifting fastest and the stakes are highest.",
        "lede_p": "Dr. Greg Brown is the founding and executive director of The Alliance Futures Initiative. He brings nearly two decades of analytic work for the US national security community, four years building a new think tank presence into a serious policy voice, and the kind of regional fluency Washington talks about valuing but rarely invests in building.",
        "sections": [
            ("Background", [
                "Before launching TAFI, Brown spent nearly two decades supporting research, analysis, and outreach programs across the US national security community. He developed research projects, designed and ran wargames and exercises, and directed regional and functional expert panels for the Office of the Director of National Intelligence, the National Intelligence Council, the Federal Foresight Community of Interest, and other national security agencies. That work gave him direct, sustained exposure to how Washington consumes intelligence, weighs alliance and partner commitments, and thinks &mdash; or fails to think &mdash; about strategic futures.",
                "Brown is an authority on political demography, comparative foreign policy, and Indo-Pacific security.",
            ]),
            ("Teaching", [
                "Since 2005, he has served as Adjunct Professor at the Center for Australian, New Zealand, and Pacific Studies in Georgetown University's School of Foreign Service, where he teaches courses on strategic competition in the Pacific, migration and conflict, national identity, and comparative foreign policy. He regularly advises undergraduate and graduate capstone projects and has served as a faculty reviewer for Truman, Marshall, and Rhodes Scholarship candidates.",
            ]),
            ("Consulting &amp; Fellowships", [
                "His consulting and fellowship appointments reflect the breadth of his regional network. Brown has served as an instructor for the State Department's Foreign Service Institute course on Australia, New Zealand, and the Pacific Islands; as a consultant for Freedom House, the Friedrich Ebert Foundation, the Centre for East European and International Studies in Berlin, and the UN Millennium Project's program on transnational organized crime.",
                "He has held appointments as a RICE Fellow at the East-West Center, a Research Fellow at the University of Melbourne's Australian Centre, and an Australian National University Parliamentary Fellow in the Office of the Shadow Minister for Immigration and Multiculturalism.",
            ]),
            ("Selected Publications &amp; Commentary", [
                "His analysis and commentary on Indo-Pacific security, political demography, and alliance dynamics have appeared in <em>The Economist</em>, <em>Nikkei Asia</em>, the <em>South China Morning Post</em>, <em>Radio Free Asia</em>, <em>Breaking Defense</em>, <em>Voice of America</em>, the <em>Mainichi Shimbun</em>, <em>The Australian</em>, and the <em>New Zealand Herald</em>.",
                "His published work includes pieces in <em>The Strategist</em>, <em>The National Interest</em>, the <em>Georgetown Journal of International Affairs</em>, <em>Political Science</em>, and <em>People and Place</em>.",
            ]),
            ("Education", [
                "Brown received his Ph.D. in Government from the University of Texas at Austin, where he was an Outstanding Graduate Instructor Award finalist. He previously held teaching and research appointments at Southwestern University and UT, Austin.",
            ]),
            ("Personal", [
                "His family ties run from Manila, Melbourne, and Tokyo to Portland, Palo Alto, and Philadelphia to Copenhagen, Cape Town, and Zurich &mdash; a geography that makes international relations personal, not just theoretical. He remains the only member of his immediate family to avoid acquiring dual citizenship.",
            ]),
        ],
        "focus": [
            "Alliance dynamics &amp; futures",
            "Indo-Pacific security",
            "Political demography",
            "Comparative foreign policy",
            "Strategic foresight",
        ],
        "affiliations": [
            "Adjunct Professor, Georgetown University SFS",
            "Founding Director, TAFI",
        ],
        "education": [
            "Ph.D., Government, University of Texas at Austin",
        ],
    },
    {
        "slug": "eric-lies",
        "name": "Eric Lies",
        "title": "Deputy Director",
        "photo": "eric-lies.jpg",
        "email": "elies@alliancefutures.org",
        "linkedin": "https://www.linkedin.com/in/eric-lies-92813b252",
        "prev": ("greg-brown", "Dr. Greg Brown"),
        "next": ("jonah-bock", "Jonah Bock"),
        "hero_lede": "Manages TAFI's daily operations and leads research on alliance systems, security strategy, and military affairs &mdash; blending Naval Academy leadership training with lived experience executing US national-security strategy.",
        "lede_p": "Eric Lies is the Deputy Director of The Alliance Futures Initiative. An accomplished national security professional and U.S. Navy veteran, he brings over fifteen years of experience to the role. Beyond overseeing daily operations and his own research priorities, he leads TAFI's institutional outreach with other think tanks, U.S. and foreign government officials, and universities.",
        "sections": [
            ("Research", [
                "An expert in national security, defense, and alliance systems, Eric utilizes structured analytics, systems analysis, and multi-disciplinary techniques throughout his research. His previous research has focused on Indo-Pacific deterrence, greyzone competition, and the AUKUS partnership.",
                "He has published widely in places such as <em>War on the Rocks</em>, <em>The National Interest</em>, and <em>The Strategist</em>, and has given comments to both <em>Newsweek</em> and <em>Foreign Policy</em>.",
            ]),
            ("Naval Career", [
                "Eric's professional foundation was built during a distinguished thirteen-year career in the United States Navy. He held several high-stakes leadership positions, including Head of Department for the Navy Data Center in Yokosuka, Japan, and as a certified Naval Nuclear Engineer and Assistant Head of Propulsion for the USS CARL VINSON.",
                "During his service, he was deployed around the world &mdash; serving in the Arabian Gulf and the South China Sea, and stationed in Yokosuka, Japan.",
            ]),
            ("Education", [
                "Eric earned a Master's in International Service from American University, where he was awarded the Louis Goodman Award for academic and scholarly excellence. He received his Bachelor of Science with Merit in International Relations and a Spanish minor from the United States Naval Academy.",
            ]),
        ],
        "focus": [
            "Alliance systems &amp; deterrence",
            "AUKUS partnership",
            "Indo-Pacific maritime strategy",
            "Greyzone competition",
            "Structured analytic techniques",
        ],
        "affiliations": [
            "Deputy Director, TAFI",
            "U.S. Navy (veteran, 13 years)",
        ],
        "education": [
            "M.A., International Service, American University",
            "B.S. (Merit), International Relations, U.S. Naval Academy",
        ],
    },
    {
        "slug": "jonah-bock",
        "name": "Jonah Bock",
        "title": "Assistant Director for Research",
        "photo": "jonah-bock.jpg",
        "email": "jbock@alliancefutures.org",
        "linkedin": "https://www.linkedin.com/in/jonah-bock-496902ba/",
        "prev": ("eric-lies", "Eric Lies"),
        "next": ("leah-markworth", "Leah Markworth"),
        "hero_lede": "Manages TAFI's research portfolio. Focus: strategic competition, Pacific Islands geopolitics, and China's influence in the region.",
        "lede_p": "Jonah Bock is the Assistant Director for Research at The Alliance Futures Initiative. His own work focuses on strategic competition, Pacific Islands geopolitics, and China's influence in the region. He brings experience spanning policy research, open-source intelligence, and futures analysis &mdash; not the kinds he reads in sci-fi.",
        "sections": [
            ("Background", [
                "Prior to joining TAFI, Jonah served as a Senior Research Assistant at the Australian Strategic Policy Institute USA, where he published widely on Pacific Islands affairs in outlets including <em>The Diplomat</em>, <em>The National Interest</em>, and <em>The Strategist</em>. His work has examined topics ranging from U.S. strategic competition with China in the Pacific to Taiwan's diplomatic relationships, naval shipbuilding policy, and the geopolitics of individual island nations such as Palau and Kiribati.",
                "He also held a virtual student federal service internship with the Department of State's East Asia and Pacific Bureau, supporting research on China's efforts to erode Taiwan's diplomatic partnerships in the Pacific.",
            ]),
            ("At TAFI", [
                "Jonah produces the PRC Pacific Embassies Monitor, a weekly open-source intelligence product providing systematic tracking of Beijing's public diplomatic activities across the nine Pacific Island Countries hosting Chinese missions.",
            ]),
            ("Education", [
                "He holds a Bachelor of Arts in International Affairs from American University's School of International Service, with a minor in Chinese Language. Jonah studied abroad in Taiwan, where he ate very well and took a couple of courses too.",
            ]),
        ],
        "focus": [
            "Pacific Islands geopolitics",
            "China's influence operations",
            "U.S.&ndash;China strategic competition",
            "Open-source intelligence",
            "Taiwan's diplomatic partnerships",
        ],
        "affiliations": [
            "Assistant Director for Research, TAFI",
            "Former Senior Research Assistant, ASPI USA",
        ],
        "education": [
            "B.A., International Affairs (Chinese minor), American University",
        ],
    },
    {
        "slug": "leah-markworth",
        "name": "Leah Markworth",
        "title": "Research Associate",
        "photo": "leah-markworth.webp",
        "email": "lmarkworth@alliancefutures.org",
        "linkedin": "https://www.linkedin.com/in/leahmarkworth/",
        "prev": ("jonah-bock", "Jonah Bock"),
        "next": ("nishank-motwani", "Dr. Nishank Motwani"),
        "hero_lede": "Focuses on Indo-Pacific affairs and partnerships, with Mandarin linguist and translation work for TAFI clients.",
        "lede_p": "Leah Markworth is a Research Associate at The Alliance Futures Initiative, focusing on Indo-Pacific affairs and partnerships, along with providing Mandarin linguist and translation services to clients.",
        "sections": [
            ("Education", [
                "Leah is currently a senior at the University of California, Berkeley, double majoring in Global Studies and Cognitive Science with a minor in Mandarin. Her academic concentration centers on Asian development, complementing her fluency in Mandarin.",
            ]),
            ("Background", [
                "Prior to joining TAFI, Leah held two roles at the Australian Strategic Policy Institute (ASPI) USA. As an Analyst Intern, she supported research on Indo-Pacific security, synthesized policy briefs, and composed literature reviews. As an Events and Communications Intern, she coordinated logistics, managed social media, and enhanced digital brand engagement.",
                "Her independent analysis has also been published in <em>The Diplomat</em>.",
            ]),
            ("China Travels &amp; Fellowship", [
                "Leah has travelled to China on several occasions, notably placing in the top 30 of the 2024 Chinese Bridge Competition and presenting research on sustainable development through the Young Envoys Scholarship Program.",
                "In the summer of 2024, she completed a fellowship with the Hudson Institute, where she analyzed political philosophy and gained practical insight into the legislative process through policy workshops.",
            ]),
            ("On Campus", [
                "Leah was Vice President of Communications for Delta Gamma's Gamma Chapter and served as Social Media and Web Chair for Delta Phi Epsilon, a professional foreign service fraternity.",
            ]),
        ],
        "focus": [
            "Indo-Pacific affairs",
            "Mandarin translation",
            "Asian development",
            "China analysis",
        ],
        "affiliations": [
            "Research Associate, TAFI",
            "Senior, UC Berkeley",
            "Former Hudson Institute Fellow (2024)",
        ],
        "education": [
            "B.A. (in progress), Global Studies &amp; Cognitive Science, Mandarin minor, UC Berkeley",
        ],
    },
    {
        "slug": "nishank-motwani",
        "name": "Dr. Nishank Motwani",
        "title": "Senior Fellow",
        "photo": "nishank-motwani.jpg",
        "email": "nmotwani@alliancefutures.org",
        "linkedin": "https://www.linkedin.com/in/nishankmotwani/",
        "prev": ("leah-markworth", "Leah Markworth"),
        "next": ("andrew-horton", "Andrew Horton"),
        "hero_lede": "Strategic advisor at the intersection of global security, emerging technology, and geopolitical risk &mdash; with significant experience across the Indo-Pacific, the Middle East, and the U.S.",
        "lede_p": "Dr. Nishank Motwani is a strategic advisor operating at the intersection of global security, emerging technology, and geopolitical risk. His career spans the &ldquo;Quad&rdquo; nations and includes significant experience in Afghanistan and the Middle East, providing executive leadership with the analytical rigor required to navigate polycrisis environments.",
        "sections": [
            ("Practice", [
                "Nishank specializes in translating complex geostrategic shifts into actionable intelligence, bridging the gap between national security policy, commercial markets, and contested spaces.",
                "Whether advising on AUKUS-related defense integration, countering adversarial grey zone activities, or analyzing the socio-political impact of disruptive technologies, he delivers high-stakes insights that protect interests and identify growth opportunities across the Indo-Pacific, the Middle East, and the U.S.",
            ]),
        ],
        "focus": [
            "AUKUS &amp; defense integration",
            "Grey zone activity",
            "Emerging technology &amp; geopolitical risk",
            "Indo-Pacific security",
            "Middle East &amp; Afghanistan",
        ],
        "affiliations": [
            "Senior Fellow, TAFI",
        ],
        "education": [
            "Ph.D.",
        ],
    },
    {
        "slug": "andrew-horton",
        "name": "Andrew Horton",
        "title": "Senior Fellow",
        "photo": "andrew-horton.jpeg",
        "email": None,
        "linkedin": "https://www.linkedin.com/in/andrew-horton-727735/",
        "prev": ("nishank-motwani", "Dr. Nishank Motwani"),
        "next": ("marc-ablong", "Marc Ablong PSM"),
        "hero_lede": "A technology founder, strategic advisor, and experienced Board Chair with over 30 years at the intersection of emerging technology and geopolitics &mdash; advising on cyber governance, artificial intelligence, and quantum strategy.",
        "lede_p": "Andrew Horton is a technology founder, strategic advisor, and experienced Board Chair, with over 30 years' experience operating at the intersection of emerging technology and geopolitics. He brings a cross-sector perspective spanning corporate, government, and not-for-profit environments, and is a recognised thought leader on national security, sovereign capability, and the geopolitical implications of advanced technologies.",
        "sections": [
            ("Career", [
                "Across his career, Andrew has founded, scaled, and transformed high-growth organisations, including the creation of an award-winning, world-first digital learning ecosystem for the university sector. His work spans industry, government, and academia, where he is valued for translating complex technological change into clear, practical strategic outcomes.",
            ]),
            ("Advisory Practice", [
                "Andrew provides trusted senior-level advice on cyber governance, artificial intelligence, and quantum strategy, supporting organisations to navigate an increasingly complex and contested global technology landscape.",
            ]),
            ("Education", [
                "He holds a double major degree in Accounting and Information Systems and a Postgraduate Certificate in Education.",
            ]),
        ],
        "focus": [
            "National security &amp; sovereign capability",
            "Cyber governance",
            "Artificial intelligence",
            "Quantum strategy",
            "Geopolitics of advanced technology",
        ],
        "affiliations": [
            "Senior Fellow, TAFI",
        ],
        "education": [
            "Double major, Accounting &amp; Information Systems",
            "Postgraduate Certificate in Education",
        ],
    },
    {
        "slug": "marc-ablong",
        "name": "Marc Ablong PSM",
        "title": "Senior Fellow",
        "photo": "marc-ablong.jpg",
        "email": None,
        "linkedin": "https://www.linkedin.com/in/marc-ablong-74936739/",
        "prev": ("andrew-horton", "Andrew Horton"),
        "next": ("austin-wu", "Austin Wu"),
        "hero_lede": "A geostrategic-risk advisor and former Australian Deputy Secretary whose 31-year public-service career spanned national security, intelligence, critical and emerging technology, cyber, and Defence strategy &mdash; including leadership of two Australian Defence White Papers.",
        "lede_p": "Marc Ablong PSM is the Managing Partner of Geostrategic Risk Partners Pty Ltd, helping organisations manage geostrategic risks and find opportunities to succeed in an uncertain world.",
        "sections": [
            ("Public Service Career", [
                "Marc left the Australian Public Service in 2024 after a 31-year career that culminated as a Deputy Secretary within the Australian Department of Home Affairs, where he held responsibility for strategic guidance and capability planning; national security policy; international relationship management; immigration policy; law enforcement policy and electronic surveillance reform; data and biometrics policy; regional processing and resettlement; emergency management; intelligence; critical and emerging technology policy; cyber security policy; national resilience and strengthening democracy.",
                "Prior to joining the Department of Home Affairs, Marc was a senior executive across 25 years within the Australian Department of Defence, where he held positions in capital equipment and acquisition policy, international policy, military strategy, maritime capability development, Air Force long-range planning, futures and scenario-planning, national support and mobilisation planning, information strategy and futures, strategic reform, Defence strategic policy, Defence industry policy, corporate governance, media and ministerial coordination, contestability, and naval shipbuilding policy. Marc was Chief of Staff of the 2009 Defence White Paper Team, providing strategic advice and support to the Principal Author, and led the development of the 2016 Defence White Paper, Integrated Investment Program, and Defence Industry Policy Statement. He left Defence after a period as acting Deputy Secretary Strategic Policy and Intelligence.",
                "Prior to joining Government service, Marc had an earlier career in the Australian banking and finance industry.",
            ]),
            ("Education &amp; Honours", [
                "Marc is a graduate of the Joint Services Staff College (1997), the Centre for Defence and Strategic Studies (2002), and the Advanced Management Program 190 (2016) at the Harvard Business School. Marc was awarded the Public Service Medal in the 2018 Australia Day Honours.",
            ]),
        ],
        "focus": [
            "Geostrategic risk",
            "National security &amp; intelligence policy",
            "Defence strategy &amp; capability planning",
            "Critical &amp; emerging technology policy",
            "Cyber security &amp; national resilience",
        ],
        "affiliations": [
            "Senior Fellow, TAFI",
            "Managing Partner, Geostrategic Risk Partners",
            "Senior Fellow, Australian Strategic Policy Institute",
            "Fellow, Helsinki Geoeconomics Society",
            "Fellow, Institute For Integrated Economic Research &mdash; Australia",
            "Fellow, Institute for Strategic Risk Management",
        ],
        "education": [
            "Joint Services Staff College (1997)",
            "Centre for Defence and Strategic Studies (2002)",
            "Advanced Management Program 190, Harvard Business School (2016)",
        ],
    },
    {
        "slug": "austin-wu",
        "name": "Austin Wu",
        "title": "Fellow",
        "photo": "austin-wu.jpg",
        "email": "awu@alliancefutures.org",
        "linkedin": "https://www.linkedin.com/in/austin-wu-87839a178/",
        "prev": ("marc-ablong", "Marc Ablong PSM"),
        "next": ("jackie-gibson", "Jackie Gibson"),
        "hero_lede": "Independent research on intelligence warfighting, Indo-Pacific deterrence, and the maritime industrial base.",
        "lede_p": "Austin Wu is a Fellow at The Alliance Futures Initiative, where he conducts independent research on intelligence warfighting, Indo-Pacific deterrence, and the maritime industrial base.",
        "sections": [
            ("Publications", [
                "His analysis has been published in outlets including <em>The Hill</em>, <em>The Strategist</em>, and <em>Real Clear Defense</em>.",
            ]),
            ("Service", [
                "Austin also serves as an intelligence officer in the U.S. Army Reserve.",
            ]),
        ],
        "focus": [
            "Intelligence warfighting",
            "Indo-Pacific deterrence",
            "Maritime industrial base",
        ],
        "affiliations": [
            "Fellow, TAFI",
            "U.S. Army Reserve, Intelligence Officer",
        ],
        "education": [],
    },
    {
        "slug": "jackie-gibson",
        "name": "Jackie Gibson",
        "title": "Fellow",
        "photo": "jackie-gibson.jpg",
        "email": "jgibson@alliancefutures.org",
        "linkedin": "https://www.linkedin.com/in/jacqueline-gibson-304a49229",
        "prev": ("austin-wu", "Austin Wu"),
        "next": None,
        "hero_lede": "Leads TAFI's work on subnational alliance dynamics and First Nations engagement in defense and economic strategy.",
        "lede_p": "Jackie Gibson is a Fellow at The Alliance Futures Initiative. She leads TAFI's work on subnational alliance dynamics and First Nations engagement in defense and economic strategy, with a focus on how sovereign communities in the United States and partner nations can shape the architecture of allied security cooperation.",
        "sections": [
            ("Background", [
                "Gibson brings a career grounded in U.S.&ndash;China strategic competition, export controls, and Indo-Pacific alliance policy, built through research and analytic work at ASPI USA and the University of Oklahoma's Institute for U.S.&ndash;China Issues.",
                "She channels that foundation into a commitment to building deeper resilience into global partnerships, championing First Nations and sovereign voices as a core pillar of modern defense strategy.",
            ]),
        ],
        "focus": [
            "Subnational alliance dynamics",
            "First Nations engagement",
            "U.S.&ndash;China strategic competition",
            "Export controls",
            "Indo-Pacific alliance policy",
        ],
        "affiliations": [
            "Fellow, TAFI",
            "Former researcher, ASPI USA",
            "Former researcher, OU Institute for U.S.&ndash;China Issues",
        ],
        "education": [],
    },
]


EMAIL_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16v16H4z"/><path d="M4 4l8 8 8-8"/></svg>'
LINKEDIN_SVG = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M20.5 2h-17A1.5 1.5 0 002 3.5v17A1.5 1.5 0 003.5 22h17a1.5 1.5 0 001.5-1.5v-17A1.5 1.5 0 0020.5 2zM8 19H5V8h3v11zM6.5 6.7a1.8 1.8 0 110-3.6 1.8 1.8 0 010 3.6zM19 19h-3v-5.6c0-3.4-4-3.1-4 0V19h-3V8h3v1.8c1.4-2.6 7-2.8 7 2.5V19z"/></svg>'


def render_bio_actions(email, linkedin):
    """Hero email/LinkedIn buttons; omit a button when its value is missing."""
    btns = []
    if email:
        btns.append(f"""                    <a href="mailto:{email}" class="bio-action">
                        {EMAIL_SVG}
                        Email
                    </a>""")
    if linkedin:
        btns.append(f"""                    <a href="{linkedin}" target="_blank" rel="noopener" class="bio-action">
                        {LINKEDIN_SVG}
                        LinkedIn
                    </a>""")
    if not btns:
        return ""
    return '                <div class="bio-actions">\n' + "\n".join(btns) + "\n                </div>"


def render_contact_card(email, linkedin):
    """Rail Contact card; omit a row when its value is missing, drop the card if both are."""
    rows = []
    if email:
        rows.append(f"""                    <a class="rail-row" href="mailto:{email}">
                        {EMAIL_SVG}
                        {email}
                    </a>""")
    if linkedin:
        rows.append(f"""                    <a class="rail-row" href="{linkedin}" target="_blank" rel="noopener">
                        {LINKEDIN_SVG}
                        LinkedIn
                    </a>""")
    if not rows:
        return ""
    return ('                <div class="rail-card">\n'
            "                    <h3>Contact</h3>\n"
            + "\n".join(rows) + "\n                </div>")


def render_section(heading, paragraphs):
    """Flattened: section headings are intentionally dropped so the bio
    reads as continuous paragraphs. The 'heading' argument is kept in the
    PEOPLE list for editorial reference only.
    """
    return "\n                ".join(f"<p>{p}</p>" for p in paragraphs)


def render_rail_card(title, items):
    if not items:
        return ""
    lis = "\n                        ".join(f"<li>{i}</li>" for i in items)
    return f"""                <div class="rail-card">
                    <h3>{title}</h3>
                    <ul>
                        {lis}
                    </ul>
                </div>"""


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} | TAFI</title>
    <meta name="description" content="{name}, {title} at The Alliance Futures Initiative.">
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Montserrat:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="../css/shared.css?v=2">
    <link rel="stylesheet" href="../css/bio.css?v=2">
</head>
<body>
    <header id="header">
        <a href="../index.html" class="logo">
            <img src="../images/tafi-logo-real.png" alt="TAFI Logo" class="logo-img">
            <div class="logo-text">
                <span class="logo-text-main">TAFI</span>
                <span class="logo-text-sub">The Alliance Futures Initiative</span>
            </div>
        </a>
        <nav>
            <a href="../about.html">About</a>
            <div class="nav-dropdown">
                <a href="../our-work/index.html" class="nav-dropdown-trigger">Our Work <svg width="10" height="6" viewBox="0 0 10 6" fill="none"><path d="M1 1L5 5L9 1" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></a>
                <div class="nav-dropdown-menu">
                    <a href="../our-work/index.html?category=research">Research</a>
                    <a href="../our-work/index.html?category=futures">Futures</a>
                    <a href="../our-work/index.html?category=commentary">Commentary</a>
                    <a href="../embassy-monitors/index.html">Embassies Monitor</a>
                </div>
            </div>
            <a href="../advisory.html">Advisory</a>
            <a href="../people.html">People</a>
            <a href="../support.html">Support</a>
        </nav>
        <div class="mobile-menu"><span></span><span></span><span></span></div>
        <nav class="mobile-nav">
            <a href="../about.html">About</a>
            <div class="mobile-nav-group">
                <button class="mobile-nav-group-trigger">Our Work <svg width="10" height="6" viewBox="0 0 10 6" fill="none"><path d="M1 1L5 5L9 1" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
                <div class="mobile-nav-group-items">
                    <a href="../our-work/index.html?category=research">Research</a>
                    <a href="../our-work/index.html?category=futures">Futures</a>
                    <a href="../our-work/index.html?category=commentary">Commentary</a>
                    <a href="../embassy-monitors/index.html">Embassies Monitor</a>
                </div>
            </div>
            <a href="../advisory.html">Advisory</a>
            <a href="../people.html">People</a>
            <a href="../support.html">Support</a>
        </nav>
    </header>

    <section class="bio-hero">
        <div class="bio-hero-inner">
            <div class="bio-portrait">
                <img src="../images/team/{photo}" alt="{name}">
            </div>
            <div class="bio-headline">
                <nav class="breadcrumb">
                    <a href="../index.html">Home</a> <span>/</span>
                    <a href="../people.html">People</a> <span>/</span>
                    <span>{name}</span>
                </nav>
                <h1>{name}</h1>
                <div class="role">{title}</div>
                <p class="lede">{hero_lede}</p>
{bio_actions}
            </div>
        </div>
    </section>

    <section class="bio-body">
        <div class="bio-body-inner">
            <article class="bio-prose">
                <p class="lede-p">{lede_p}</p>

{sections_html}

{recent_work_section}
            </article>

            <aside class="bio-rail">
{contact_card}
{focus_card}
{affiliations_card}
{education_card}
            </aside>
        </div>
    </section>

    <section class="bio-nav-section">
        <nav class="bio-nav">
            {prev_link}
            {next_link}
        </nav>
    </section>

    <footer>
        <div class="container">
            <div class="footer-content">
                <div class="footer-logo">
                    <img src="../images/tafi-logo-real.png" alt="TAFI">
                    <span class="footer-logo-text">TAFI</span>
                </div>
                <div class="footer-links">
                    <a href="../about.html">About</a>
                    <a href="../our-work/index.html">Our Work</a>
                    <a href="../advisory.html">Advisory</a>
                    <a href="../people.html">People</a>
                    <a href="../support.html">Support</a>
                    <a href="../index.html#contact">Contact</a>
                </div>
            </div>
            <div class="footer-bottom">
                <!-- PLACEHOLDERS to confirm before launch: mailing address, contact@ -->
                <p style="max-width: 900px; margin: 0 auto 1rem; font-size: 0.85rem; line-height: 1.7;">
                    TAFI is supported by foundation grants, individual donors, and commercial advisory work, with a strict firewall between commercial engagements and our public research.
                </p>
                <p style="max-width: 900px; margin: 0 auto 1rem; font-size: 0.8rem; line-height: 1.7; opacity: 0.85;">
                    The Alliance Futures Initiative is a research program of OTX International, an independent, non-partisan 501(c)(3) public charity. Contributions are tax-deductible to the fullest extent permitted by law.
                </p>
                <p style="font-size: 0.8rem; opacity: 0.8;">
                    <a href="mailto:contact@alliancefutures.org" style="color: var(--ocean-light);">contact@alliancefutures.org</a>
                </p>
                <p style="margin-top: 1rem;">&copy; 2026 The Alliance Futures Initiative &middot; Founded 2026 &middot; <a href="../privacy.html" style="color: var(--ocean-light);">Privacy</a></p>
            </div>
        </div>
    </footer>

    <script>
        const header = document.getElementById('header');
        window.addEventListener('scroll', () => {{
            header.classList.toggle('scrolled', window.scrollY > 100);
        }});
        const mobileMenu = document.querySelector('.mobile-menu');
        const mobileNav = document.querySelector('.mobile-nav');
        mobileMenu.addEventListener('click', () => {{
            mobileMenu.classList.toggle('active');
            mobileNav.classList.toggle('active');
        }});
        document.querySelectorAll('.mobile-nav a').forEach(l => l.addEventListener('click', () => {{
            mobileMenu.classList.remove('active'); mobileNav.classList.remove('active');
        }}));
        document.querySelectorAll('.mobile-nav-group-trigger').forEach(t => t.addEventListener('click', () => {{
            t.classList.toggle('active'); t.nextElementSibling.classList.toggle('active');
        }}));
        // Recent Work expand/collapse
        document.querySelectorAll('.rw-toggle').forEach(btn => {{
            btn.addEventListener('click', () => {{
                const expanded = btn.getAttribute('aria-expanded') === 'true';
                btn.setAttribute('aria-expanded', String(!expanded));
                const list = btn.previousElementSibling;
                if (list && list.classList.contains('recent-work-list')) {{
                    list.classList.toggle('is-expanded', !expanded);
                }}
            }});
        }});
    </script>
</body>
</html>
"""


def build():
    recent_by_author = load_recent_work()
    total_items = sum(len(v) for v in recent_by_author.values())
    print(f"Loaded {total_items} recent-work entries across {len(recent_by_author)} authors.")

    for p in PEOPLE:
        sections_html = "\n\n".join(render_section(h, ps) for h, ps in p["sections"])
        focus_card = render_rail_card("Areas of Focus", p["focus"])
        affiliations_card = render_rail_card("Affiliations", p["affiliations"])
        education_card = render_rail_card("Education", p["education"])

        recent_items = recent_by_author.get(p["slug"], [])
        recent_work_section = render_recent_work_section(p["slug"], recent_items)

        bio_actions = render_bio_actions(p.get("email"), p.get("linkedin"))
        contact_card = render_contact_card(p.get("email"), p.get("linkedin"))

        prev_link = (f'<a href="{p["prev"][0]}.html" class="prev">&larr; {p["prev"][1]}</a>'
                     if p["prev"] else '<a href="../people.html" class="prev">&larr; All People</a>')
        next_link = (f'<a href="{p["next"][0]}.html" class="next">{p["next"][1]} &rarr;</a>'
                     if p["next"] else '<a href="../people.html" class="next">All People &rarr;</a>')

        html = PAGE.format(
            name=p["name"], title=p["title"], photo=p["photo"],
            hero_lede=p["hero_lede"], lede_p=p["lede_p"],
            sections_html=sections_html,
            recent_work_section=recent_work_section,
            bio_actions=bio_actions,
            contact_card=contact_card,
            focus_card=focus_card,
            affiliations_card=affiliations_card,
            education_card=education_card,
            prev_link=prev_link, next_link=next_link,
        )
        out = OUT / f"{p['slug']}.html"
        out.write_text(html)
        n = len(recent_items)
        print(f"wrote {p['slug']}.html  ({n} recent {'item' if n == 1 else 'items'})")


if __name__ == "__main__":
    build()
