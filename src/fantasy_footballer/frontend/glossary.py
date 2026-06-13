"""Glossary page — the platform's lexicon of terms, metrics, and concepts (one source of truth)."""

from backend.db import DbManager
from frontend.utils import SECTION_COLORS, common_header
from nicegui import ui

# Reading order of the category clusters; colors come from the shared SECTION_COLORS catalog.
CATEGORY_ORDER = ["General", "Scoring", "Matchups", "Luck", "Shotgun", "Clutch",
                  "Lineups", "Roster", "Postseason", "Draft", "Transactions", "Schedule"]


def _terms():
    """All glossary rows (slug/term/category/short_def/full_def/related), ordered by category, term."""
    return DbManager.query(
        "select slug, term, category, short_def, full_def, related from main_marts.glossary "
        "order by category, term", to_dict=True)


def _scroll_to(slug):
    """Smooth-scroll the page to a term's card (used by related-term chips, same-page jumps)."""
    ui.run_javascript(f"document.getElementById('{slug}')?.scrollIntoView({{behavior:'smooth',block:'start'}})")


def _term_card(term, color, term_names):
    """One term: an anchored card with the full definition and cross-link chips for related terms."""
    with ui.card().classes("w-full p-4 gap-1 rounded-xl shadow-sm").props(f'id={term["slug"]}'):
        ui.label(term["term"]).classes(f"text-lg font-semibold text-{color}-8")
        ui.label(term["full_def"]).classes("text-sm opacity-80")
        related = [slug for slug in (term["related"] or "").split(",") if slug]
        if related:
            with ui.row().classes("items-center gap-2 mt-1 no-wrap flex-wrap"):
                ui.label("Related").classes("text-xs uppercase tracking-wide opacity-40 shrink-0")
                for slug in related:
                    chip = ui.chip(term_names.get(slug, slug), color=f"{color}-1").props("dense") \
                        .classes(f"cursor-pointer text-{color}-8")
                    chip.on("click", lambda bound_slug=slug: _scroll_to(bound_slug))


@ui.refreshable
def term_sections(terms, query):
    """Render the category sections, filtered to terms matching the search query (term or definition)."""
    needle = (query or "").strip().lower()
    matches = [
        term for term in terms
        if not needle or needle in term["term"].lower()
        or needle in term["short_def"].lower() or needle in term["full_def"].lower()
    ]
    if not matches:
        ui.label("No terms match your search").classes("mx-auto text-gray-500 py-10")
        return
    term_names = {term["slug"]: term["term"] for term in terms}
    by_category = {}
    for term in matches:
        by_category.setdefault(term["category"], []).append(term)
    for category in CATEGORY_ORDER:
        category_terms = by_category.get(category)
        if not category_terms:
            continue
        color = SECTION_COLORS.get(category, "grey")
        ui.label(category).classes(f"text-xl font-bold text-{color}-7 w-full mt-6 mb-1")
        for term in category_terms:
            _term_card(term, color, term_names)


@ui.page("/glossary")
def page():
    """Glossary page: a searchable, category-grouped reference of every term across the platform."""
    common_header()
    terms = _terms()
    with ui.column().classes("w-full items-center px-8 py-6"):
        with ui.column().classes("max-w-4xl w-full gap-2"):
            ui.label("Glossary").classes("text-4xl font-semibold w-full text-center")
            ui.label("Every term, metric, and concept across the platform — defined once.").classes(
                "text-base opacity-60 w-full text-center mb-2")
            search = ui.input(placeholder="Search terms…").props("outlined dense clearable") \
                .classes("w-full max-w-md mx-auto")
            search.on_value_change(lambda: term_sections.refresh(terms, search.value))
            term_sections(terms, "")
    # Deep-link support: if the URL carries a #slug (e.g. from a metric card), scroll to it once the
    # cards have rendered.
    ui.timer(0.3, lambda: ui.run_javascript(
        "if(location.hash){const el=document.getElementById(location.hash.slice(1));"
        "if(el)el.scrollIntoView({behavior:'smooth',block:'start'});}"), once=True)
