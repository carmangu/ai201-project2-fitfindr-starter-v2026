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
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    # session = new_session(query, wardrobe)

    # # TODO: delete these two lines and build the loop.
    # session["error"] = "The planning loop isn't built yet — see the TODO in agent.py."
    # return session
    
    session = new_session(query, wardrobe)

    # 1. Parse the query
    session["parsed"] = parse_query(query)

    # 2. Count iterations, check against MAX_ITERATIONS
    count = 0
    trace.check_iterations(count)

    # 3. Search listings
    results = search_listings(
        description=session["parsed"]["description"],
        size=session["parsed"]["size"],
        max_price=session["parsed"]["max_price"],
    )
    session["search_results"] = results

    # 4. BRANCH: if empty, stop
    if not results:
        parsed = session["parsed"]
        suggestions = []
        if parsed["size"] is not None:
            suggestions.append(f"try a different size (you asked for {parsed['size']})")
        if parsed["max_price"] is not None:
            suggestions.append(f"raise your price ceiling (${parsed['max_price']})")
        suggestions.append("or use fewer keywords in your description")
        session["error"] = (
            f"No listings matched '{parsed['description']}'. "
            f"Try one of: {'; '.join(suggestions)}."
        )
        return session

    # 5. Choose the first result
    session["selected_item"] = results[0]

    # 6. Suggest outfit
    count += 1
    trace.check_iterations(count)
    session["outfit_suggestion"] = suggest_outfit(
        session["selected_item"], session["wardrobe"]
    )

    # 7. Create fit card
    count += 1
    trace.check_iterations(count)
    session["fit_card"] = create_fit_card(
        session["outfit_suggestion"], session["selected_item"]
    )

    # 8. Return
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
