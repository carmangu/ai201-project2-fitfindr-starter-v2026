"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

from mcp_client import call_tool
import re
import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def parse_query(query: str) -> dict:
    """Parse a plain-language query into description, size, max_price."""
    parsed = {"description": query, "size": None, "max_price": None}

    # Extract "under $N" or "under N"
    price_match = re.search(r"under\s+\$?(\d+(?:\.\d+)?)", query, re.IGNORECASE)
    if price_match:
        parsed["max_price"] = float(price_match.group(1))

    # Extract "size X" where X is alphanumeric
    size_match = re.search(r"size\s+([A-Za-z0-9/]+)", query, re.IGNORECASE)
    if size_match:
        parsed["size"] = size_match.group(1)

    # Description: query minus the price and size clauses
    desc = query
    if price_match:
        desc = desc[:price_match.start()] + desc[price_match.end():]
    if size_match:
        desc = desc[:size_match.start()] + desc[size_match.end():]
    # Clean up trailing commas, "and", etc.
    desc = re.sub(r"\s+", " ", desc).strip(" ,.")
    parsed["description"] = desc

    return parsed

def run_agent(query: str, wardrobe: dict) -> dict:
    session = new_session(query, wardrobe)
    session["parsed"] = parse_query(query)
    count = 0
    trace.check_iterations(count)

    session["search_results"] = call_tool("search_listings", {
        "description": session["parsed"]["description"],
        "size": session["parsed"]["size"],
        "max_price": session["parsed"]["max_price"],
    })
    trace.step("search_listings (via MCP)",
               inputs=session["parsed"],
               returned=session["search_results"])

    if not session["search_results"]:
        p = session["parsed"]
        hints = []
        if p["size"] is not None:
            hints.append(f"try a different size (you asked for {p['size']})")
        if p["max_price"] is not None:
            hints.append(f"raise your price ceiling (${p['max_price']})")
        hints.append("use fewer keywords in your description")
        session["error"] = (
            f"No listings matched '{p['description']}'. Try one of: "
            + "; ".join(hints) + "."
        )
        trace.step("branch", note="empty search, stopping before suggest_outfit")
        return session

    session["selected_item"] = session["search_results"][0]

    count += 1
    trace.check_iterations(count)
    try:
        session["outfit_suggestion"] = suggest_outfit(
            session["selected_item"], session["wardrobe"]
        )
        trace.step("suggest_outfit",
                   inputs={"new_item": session["selected_item"]["id"],
                           "wardrobe_items": len(session["wardrobe"].get("items", []))},
                   returned=session["outfit_suggestion"])
    except ModelUnavailable as exc:
        session["error"] = (
            f"The model couldn't be reached while styling this item. "
            f"Check your internet connection or API key, then try again. "
            f"(Details: {exc})"
        )
        trace.step("suggest_outfit", note=f"ModelUnavailable: {exc}")
        return session

    count += 1
    trace.check_iterations(count)
    try:
        session["fit_card"] = create_fit_card(
            session["outfit_suggestion"], session["selected_item"]
        )
        trace.step("create_fit_card",
                   inputs={"new_item": session["selected_item"]["id"],
                           "outfit_len": len(session["outfit_suggestion"])},
                   returned=session["fit_card"])
    except ModelUnavailable as exc:
        session["error"] = (
            f"The model couldn't be reached while writing the fit card. "
            f"Check your internet connection or API key, then try again. "
            f"(Details: {exc})"
        )
        trace.step("create_fit_card", note=f"ModelUnavailable: {exc}")
        return session

    return session

# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
