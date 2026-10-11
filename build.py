"""Builds index.html from content.md. Run: python3 build.py"""
import html, re, sys
from pathlib import Path

HERE = Path(__file__).parent
FIELD = re.compile(r"^([A-Z][A-Za-z ]{1,30}):\s+(.*)$")
KNOWN = {"page title", "description", "formspree id", "email subject", "eyebrow", "headline", "intro",
         "main button", "second button", "heading", "note", "small print", "warning", "message label",
         "message hint", "button", "success message", "type", "business name", "location"}


def inline(text):
    """Escape HTML, then apply **bold** and [text](url)."""
    t = html.escape(text, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', t)
    return t


def attr(text):
    return html.escape(text, quote=True)


def slug(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:40]


class Block:
    """A '#' section or '##' subsection: fields, paragraphs, list items, table rows."""
    def __init__(self, title):
        self.title = title
        self.fields, self.paras, self.items, self.ordered, self.rows = {}, [], [], [], []
        self.subs = []

    def get(self, key, default=""):
        return self.fields.get(key.lower(), default)


def parse(md):
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    sections, cur, sub, para = {}, None, None, []

    def flush():
        if para and (sub or cur):
            (sub or cur).paras.append(" ".join(para))
        para.clear()

    for raw in md.splitlines():
        line = raw.strip()
        target = sub or cur
        if line.startswith("## "):
            flush()
            sub = Block(line[3:].strip())
            cur.subs.append(sub)
        elif line.startswith("# "):
            flush()
            cur = Block(line[2:].strip())
            sections[cur.title.lower()] = cur
            sub = None
        elif not line:
            flush()
        elif target is None:
            continue
        elif line.startswith("|"):
            flush()
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                target.rows.append(cells)
        elif line.startswith("- "):
            flush()
            target.items.append(line[2:].strip())
        elif re.match(r"^\d+\.\s", line):
            flush()
            target.ordered.append(re.sub(r"^\d+\.\s+", "", line))
        elif FIELD.match(line) and not para and FIELD.match(line).group(1).lower() in KNOWN:
            k, v = FIELD.match(line).groups()
            target.fields[k.lower()] = v
        else:
            para.append(line)
    flush()
    return sections


def need(sections, name):
    if name.lower() not in sections:
        sys.exit(f"content.md is missing the '# {name}' section.")
    return sections[name.lower()]


def build(s):
    st, hero, svc, fees = need(s, "Settings"), need(s, "Hero"), need(s, "Services"), need(s, "Fees")
    about, how, form, foot = need(s, "About"), need(s, "How it works"), need(s, "Form"), need(s, "Footer")

    cards = "\n".join(
        f'        <article class="card">\n          <h3>{inline(b.title)}</h3>\n'
        f'          <p>{inline(" ".join(b.paras))}</p>\n        </article>'
        for b in svc.subs)

    tables = []
    for b in fees.subs:
        rows = "\n".join(
            f'            <tr><th scope="row">{inline(r[0])}</th><td>{inline(r[1] if len(r) > 1 else "")}</td></tr>'
            for r in b.rows)
        tables.append(f'        <table class="fee-table">\n          <caption>{inline(b.title)}</caption>\n'
                      f'          <tbody>\n{rows}\n          </tbody>\n        </table>')

    about_paras = "\n".join(f"        <p>{inline(p)}</p>" for p in about.paras)
    about_list = ("\n        <ul class=\"facts\">\n" +
                  "\n".join(f"          <li>{inline(i)}</li>" for i in about.items) +
                  "\n        </ul>") if about.items else ""
    steps = "\n".join(f"        <li>{inline(i)}</li>" for i in how.ordered)

    checks, selects = [], []
    for q in form.subs:
        kind = q.get("type", "checkboxes").lower()
        legend = q.title
        hint = ""
        m = re.match(r"^(.*?)\s*\((.+)\)$", legend)
        if m:
            legend, hint = m.group(1), f' <span class="opt">({inline(m.group(2))})</span>'
        name = slug(legend)
        if kind.startswith("drop"):
            opts = "\n".join(f"              <option>{inline(o)}</option>" for o in q.items)
            selects.append(f'          <label>{inline(legend)}\n            <select name="{name}">\n'
                           f'              <option value="">Select one</option>\n{opts}\n            </select>\n          </label>')
        else:
            boxes = "\n".join(f'          <label class="check"><input type="checkbox" name="{name}" value="{attr(o)}"> {inline(o)}</label>'
                              for o in q.items)
            checks.append(f"        <fieldset>\n          <legend>{inline(legend)}{hint}</legend>\n{boxes}\n        </fieldset>")
    select_rows = "\n".join(
        '        <div class="row2">\n' + "\n".join(selects[i:i + 2]) + "\n        </div>"
        for i in range(0, len(selects), 2))

    return TEMPLATE.format(
        title=attr(st.get("page title")), desc=attr(st.get("description")),
        form_id=attr(st.get("formspree id", "YOUR_FORM_ID")), subject=attr(st.get("email subject")),
        eyebrow=inline(hero.get("eyebrow")), headline=inline(hero.get("headline")), intro=inline(hero.get("intro")),
        btn1=inline(hero.get("main button")), btn2=inline(hero.get("second button")),
        svc_h=inline(svc.get("heading", "Services")), cards=cards, svc_note=inline(svc.get("note")),
        fees_h=inline(fees.get("heading", "Fees")), fees_intro=inline(fees.get("intro")),
        fees_small=inline(fees.get("small print")), tables="\n".join(tables),
        about_h=inline(about.get("heading", "About")), about_paras=about_paras, about_list=about_list,
        how_h=inline(how.get("heading", "How it works")), steps=steps,
        form_h=inline(form.get("heading")), form_intro=inline(form.get("intro")), warning=inline(form.get("warning")),
        checks="\n\n".join(checks), selects=select_rows,
        msg_label=inline(form.get("message label")), msg_hint=attr(form.get("message hint")),
        submit=inline(form.get("button", "Send")),
        success=attr(form.get("success message", "Thanks. Your request is on its way.")),
        biz=inline(foot.get("business name")), loc=inline(foot.get("location")),
    ).replace("__SCRIPT__", SCRIPT)


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{desc}">
  <link rel="icon" href="assets/favicon.png">
  <link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Zilla+Slab:wght@600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="styles.css">
</head>
<body>
<!-- Generated from content.md by build.py. Edit content.md, not this file. -->

<header class="site-header">
  <div class="wrap header-row">
    <a href="#top" class="brand" aria-label="Home">
      <img src="assets/logo-navy.png" alt="Trinity Tax Group" width="158" height="43">
    </a>
    <nav aria-label="Main">
      <a href="#services">{svc_h}</a>
      <a href="#fees">{fees_h}</a>
      <a href="#about">{about_h}</a>
      <a href="#contact" class="btn btn-small">Get started</a>
    </nav>
  </div>
</header>

<main id="top">

  <section class="hero">
    <div class="wrap hero-grid">
      <div>
        <p class="eyebrow">{eyebrow}</p>
        <h1>{headline}</h1>
        <p class="lede">{intro}</p>
        <div class="hero-actions">
          <a href="#contact" class="btn">{btn1}</a>
          <a href="#fees" class="btn btn-ghost">{btn2}</a>
        </div>
      </div>
      <img class="hero-mark" src="assets/mark-white.png" alt="" width="219" height="323">
    </div>
  </section>

  <section id="services" class="section">
    <div class="wrap">
      <h2>{svc_h}</h2>
      <div class="cards">
{cards}
      </div>
      <p class="note">{svc_note}</p>
    </div>
  </section>

  <section id="fees" class="section section-alt">
    <div class="wrap fees-grid">
      <div>
        <h2>{fees_h}</h2>
        <p>{fees_intro}</p>
        <p class="small">{fees_small}</p>
      </div>
      <div>
{tables}
      </div>
    </div>
  </section>

  <section id="about" class="section">
    <div class="wrap about-grid">
      <img class="headshot" src="assets/ryan.jpg" alt="Ryan Kilpatrick" width="320" height="322">
      <div>
        <h2>{about_h}</h2>
{about_paras}{about_list}
      </div>
    </div>
  </section>

  <section class="section section-alt">
    <div class="wrap">
      <h2>{how_h}</h2>
      <ol class="steps">
{steps}
      </ol>
    </div>
  </section>

  <section id="contact" class="section">
    <div class="wrap contact-grid">
      <div>
        <h2>{form_h}</h2>
        <p>{form_intro}</p>
        <p class="warning">{warning}</p>
      </div>

      <form id="intake" class="form" action="https://formspree.io/f/{form_id}" method="POST" data-success="{success}">
        <input type="hidden" name="_subject" value="{subject}">
        <div class="hp" aria-hidden="true">
          <label>Leave this empty <input type="text" name="_gotcha" tabindex="-1" autocomplete="off"></label>
        </div>

        <div class="row2">
          <label>Full name
            <input type="text" name="name" required autocomplete="name">
          </label>
          <label>Email
            <input type="email" name="email" required autocomplete="email">
          </label>
        </div>
        <div class="row2">
          <label><span>Phone <span class="opt">(optional)</span></span>
            <input type="tel" name="phone" autocomplete="tel">
          </label>
          <label>Town and state
            <input type="text" name="location" placeholder="e.g. Westerly, RI">
          </label>
        </div>

{checks}

{selects}

        <label>{msg_label}
          <textarea name="message" rows="4" placeholder="{msg_hint}"></textarea>
        </label>

        <button type="submit" class="btn">{submit}</button>
        <p class="form-status" role="status" aria-live="polite"></p>
      </form>
    </div>
  </section>

</main>

<footer class="site-footer">
  <div class="wrap footer-row">
    <img src="assets/logo-white.png" alt="Trinity Tax Group" width="140" height="38">
    <p>{biz}<br>{loc}</p>
    <p><a href="privacy.html">Privacy notice</a></p>
  </div>
</footer>

__SCRIPT__
</body>
</html>
"""

SCRIPT = """<script>
  // Submit without leaving the page. Falls back to a normal POST if JS is off.
  const form = document.getElementById('intake');
  const status = form.querySelector('.form-status');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = form.querySelector('button');
    btn.disabled = true;
    status.textContent = 'Sending...';
    try {
      const res = await fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: { 'Accept': 'application/json' }
      });
      if (res.ok) {
        form.reset();
        status.textContent = form.dataset.success;
      } else {
        status.textContent = 'Something went wrong. Please try again in a minute.';
      }
    } catch (err) {
      status.textContent = 'Something went wrong. Please check your connection and try again.';
    }
    btn.disabled = false;
  });
</script>"""

if __name__ == "__main__":
    out = build(parse((HERE / "content.md").read_text(encoding="utf-8")))
    (HERE / "index.html").write_text(out, encoding="utf-8")
    print("Built index.html from content.md")
