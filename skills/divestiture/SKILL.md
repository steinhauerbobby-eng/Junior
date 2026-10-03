---
name: divestiture
description: Analyzes corporate divestitures of all types. Usage: /divestiture [TICKER] [type] where type is one of: spinoff, carveout, assetsale, splitoff. Use the parent company ticker.
when_to_use: Use when a company announces or is expected to execute any form of divestiture. Type flag determines the analytical framework.
---

The user will provide a ticker and a type flag. Run the **Special Situations Analyst** agent in the mode matching the type flag:

- `spinoff` → **SPINOFF mode**
- `carveout` → **CARVEOUT mode**
- `assetsale` → **ASSETSALE mode**
- `splitoff` → **SPLITOFF mode**

If no type flag is provided, ask the user which type before proceeding.

Synthesize the agent output into the report below.

---

## DIVESTITURE — {TICKER} ({TYPE})
**{Date}**

### Transaction Overview
[1 paragraph: what's being separated or sold, strategic rationale, expected timeline]

---

### Common Analysis

**Estimated value of divested asset:** [Methodology and range]

**Strategic rationale:** [Simplification / balance sheet repair / regulatory requirement / activist-driven / end of integration period]

**Key risks to completion:** [Regulatory / financing / shareholder vote / market conditions]

**Milestones & timeline:**
- [Filing date / SEC review / shareholder vote / distribution date / expected close]

---

### Type-Specific Analysis

[Full output from Special Situations Analyst for the relevant mode — see agent for complete field list by type]

---

### Verdict
[2-3 sentences: where is the opportunity — in the parent, the divested asset, or both? What is the single most important variable to monitor?]
