# RKNHS Desktop UI — Ultra-Tech Dark

Visual contract for the RKNHS Windows desktop app. Dark terminal / network-HUD aesthetic. Light themes remain supported but are **not recommended** as the primary look — prefer dark for HUD mono captions, phosphor dots, and void panels.

## Intent

- **Who:** operator of DPI / network tooling at a dense workbench screen.
- **Task:** start/stop modes, read status, change presets — one focal action per view.
- **Feel:** cold, precise, programmable — not soft Fluent, not marketing chrome.

## Signature

Corner brackets on panels + `// SECTION` mono headings + phosphor status dots + left cyan nav rail.

## Feel (hacker console)

Operator workbench for packet/DPI tooling: denser than Fluent, sharper than Win11, no soft pills. Think CRT terminal chrome without neon glow spam.

## Implementation note (Windows / Fluent)

qfluentwidgets paints cards, setting rows, and nav items with `QPainter` — plain window QSS alone barely changes the look. The desktop shell must:

1. Use solid void `#0A0C10` (amoled / mica off) so the palette is visible.
2. Patch Fluent paint paths (`ui/tech_fluent_patches.py`) for panel fills.
3. Append overrides via `setCustomStyleSheet` (`ui/tech_style.py`).
4. Set nav `setIndicatorColor` to accent cyan after the sidebar is built.

## Palette (dark)

| Token | Value | Role |
| --- | --- | --- |
| `void` | `#0A0C10` | Window / deepest background |
| `panel` | `#12151C` | Cards, sidebar, elevated surfaces |
| `panel_hover` | `#181C26` | Hover fill |
| `hairline` | `rgba(255,255,255,0.10)` | Borders |
| `hairline_strong` | `rgba(92,214,255,0.35)` | Focus / selected border |
| `fg` | `rgba(235,242,250,0.94)` | Primary text |
| `fg_muted` | `rgba(180,194,210,0.72)` | Secondary |
| `fg_faint` | `rgba(140,156,176,0.48)` | Meta / labels |
| `accent` | `#5CD6FF` | Terminal cyan |
| `accent_fg` | `#0A0C10` | Text on solid accent |
| `ok` | `#3DDC97` | Running / success |
| `warn` | `#F0B429` | Warning |
| `err` | `#FF5C7A` | Error / stopped hard |

No purple gradients. No cream. Glow is never the primary affordance — prefer border + fill.

## Typography

- **UI:** `'Segoe UI Variable', 'Segoe UI', sans-serif`
- **Mono / HUD labels:** `'Cascadia Mono', 'Consolas', 'Courier New', monospace`
- Body ~13–14px. Micro-labels 10–11px, uppercase, letter-spacing ~0.06em, weight 500–600.
- Numbers that matter (status, versions): tabular where possible; mono for code/logs.

## Density & shape

- Workbench padding: **12–16px** inside panels; **8–12px** between related controls; **20–24px** between sections.
- Radius: **2px** controls, **4–6px** panels. Never pill / `999px`.
- Cards: flat or near-flat fill + hairline. Avoid milky multi-stop gradients.

## Controls

- **Primary:** solid cyan fill, dark text, hover slightly lighter, press slightly darker. Height ~32–36px.
- **Secondary / ghost:** transparent + hairline border, muted text; hover raises border opacity.
- **Toggle:** compact track, square-ish thumb (radius 2–3), accent when on.
- **Focus:** 1px cyan ring / border, not thick glow.

## Navigation

- Dense sidebar on `void` / `panel`.
- Selected item: left cyan rail (2–3px) + soft accent fill.
- Section headers: mono uppercase micro-labels.

## Motion

- Master toggle in settings still gates all motion (`animation_policy`).
- Budget: **120–180ms**, ease-out, only `opacity` / `transform`.
- Page enter: opacity 0→1 ~150ms.
- Primary press: scale ~0.98 ≤120ms.
- Status pulse: short phosphor blink on the existing status dot.
- No layout width/height animation. No full-window glow.

## Do / Don't

**Do:** high contrast text, one accent per view, hairlines, mono for system state.  
**Don't:** purple themes, soft Win11 pills, multi-layer shadows, emoji ornaments, dashboard clutter in the first viewport of control pages.
