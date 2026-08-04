# Moorhouse UI Standard

A cross-product design standard for Moorhouse software. Any application built
under the Moorhouse brand — Summit, future consulting-delivery tools, future
client-facing SaaS — should conform to this document so that the family of
products looks, feels, and behaves like one firm.

This standard codifies the visual layer of **Summit** as the reference
implementation and generalises it for reuse. When a new product is built, this
document is the contract: tokens, components, spacing, motion, and accessibility
rules ship as shared foundations and are not re-designed per product.

---

## 0. How to use this document

- **Designers** — use the tokens, type scale, spacing scale, and component
  specs as the starting point for any new screen. Do not invent variants.
- **Engineers** — the tokens map directly to CSS custom properties and Tailwind
  utilities. Component specs map directly to the React components in
  `components/ui/*`. When you need a new component, extend the rules in §8
  rather than inventing a new visual language.
- **Contributors outside Moorhouse** — read §1 (Principles) and §2 (Brand
  foundations) first. They carry the most weight.

Version: 1.0 · Owner: Moorhouse · Last updated: 2026-04-24

---

## 1. Design principles

Six principles. When a decision is ambiguous, these are the tiebreakers.

1. **Credible, not flashy.** We are a management consultancy. The product
   should read as considered, numerate, and precise — closer to a boardroom
   deliverable than a consumer app. Avoid gradients, glass effects, heavy drop
   shadows, decorative illustration, and marketing-style hero treatments inside
   working views.
2. **Data first.** Numbers, status, and decisions carry the screen. Chrome
   recedes. Typography and whitespace do the work of borders and colour.
3. **Calm by default, loud on exception.** Green/amber/red, brand orange, and
   destructive red are reserved for *meaning*. A screen with no problems should
   be almost monochrome.
4. **Dense where experts work, generous where decisions are made.** Working
   views (lists, tables, boards) are information-dense. Exec views (dashboards,
   handoff packs, steering-committee packs) are editorial and generous.
5. **Accessible as a baseline, not an afterthought.** WCAG 2.1 AA is the floor.
   Keyboard parity with mouse. Focus is always visible. Colour is never the
   only signal.
6. **One family, many products.** Products may differ in scope and vocabulary;
   they should not differ in typography, spacing, component shape, or motion.

---

## 2. Brand foundations

### 2.1 Logo

- **Primary mark:** Moorhouse logo (`/public/brand/logo.svg`) in brand teal
  (`--brand-accent`, `#00ab8e`) on light surfaces; same mark in
  `--brand-contrast` (white) on dark or brand-purple surfaces.
- **Wordmark:** The product name is set in Poppins 600, tracked tight
  (`letter-spacing: -0.01em`), sized to match the mark's cap height.
- **Clearspace:** Minimum clearspace around the mark = 0.5× mark height on all
  sides.
- **Minimum size:** 24px square for the mark alone; 28px when accompanied by a
  wordmark.
- **Don't:** rotate the mark, recolour it outside brand teal / white, drop-
  shadow it, place it on a photographic background, or combine it with a
  product name in a non-brand typeface.

### 2.2 Tone of voice (placeholder)

The written tone of voice follows the Moorhouse Tone of Voice Guide (to be
inserted). At minimum, UI microcopy should be:

- Plainspoken, second-person ("Create initiative", not "Initiative creation").
- Declarative in headings, imperative in buttons.
- No exclamation marks in product UI. No emoji in product UI.
- Sentence case everywhere except proper nouns, acronyms, and button labels
  that are verb-first. Avoid Title Case.
- British English spelling (realise, prioritise, colour, centre).

> **TODO:** replace this subsection with the full Moorhouse Tone of Voice Guide
> when available.

---

## 3. Colour

### 3.1 Palette

| Token               | Hex       | Role                                                   |
| ------------------- | --------- | ------------------------------------------------------ |
| `--brand`           | `#3c1053` | Primary — deep purple. Headers, primary buttons, nav.  |
| `--brand-contrast`  | `#ffffff` | Text/icon on `--brand` surfaces.                       |
| `--brand-accent`    | `#00ab8e` | Teal — confirm, approve, success, focus rings.         |
| `--brand-purple`    | `#5c068c` | Hover/active state for `--brand`.                      |
| `--brand-muted`     | `#bdb6b9` | Neutral grey — dividers, disabled states, secondary UI. |
| `--brand-orange`    | `#e48949` | Secondary — attention without alarm, overlaps edge in graphs. |
| `--brand-ocean`     | `#186e7e` | Secondary — hover/active for `--brand-accent`.         |

The palette is intentionally narrow. Do not extend it with arbitrary tints.
When you need a tint, use opacity modifiers on the canonical token
(`brand/5`, `brand/10`, `brand/20`) so the relationship to the brand colour is
preserved.

### 3.2 Semantic tokens

Semantic tokens sit on top of the palette so meaning survives a palette
refresh.

| Token                | Light mode     | Dark mode       | Used for                                  |
| -------------------- | -------------- | --------------- | ----------------------------------------- |
| `--background`       | `#fbfafb`      | `#140b1a`       | Page background                           |
| `--foreground`       | `#181018`      | `#f2ecf2`       | Default text                              |
| `--surface`          | `#ffffff`      | `#1b1124`       | Cards, modals, elevated panels            |
| `--surface-muted`    | `#f5f3f6`      | `#231530`       | Sidebars, table header rows, subtle wells |
| `--border`           | `brand / 10%`  | `brand-contrast / 10%` | Default dividers and component borders   |
| `--border-strong`    | `brand / 20%`  | `brand-contrast / 20%` | Emphasised borders, secondary buttons   |
| `--text-muted`       | `#71717a`      | `#a1a1aa`       | Hints, captions, metadata                 |
| `--focus-ring`       | `--brand-accent` | `--brand-accent` | All focus outlines                       |

### 3.3 Status colours (RAG + feedback)

| Status     | Surface   | Text      | Usage                                                      |
| ---------- | --------- | --------- | ---------------------------------------------------------- |
| Green (OK) | `#dcfce7` | `#166534` | RAG green, success toasts, confirmed state                 |
| Amber      | `#fef3c7` | `#92400e` | RAG amber, warnings, attention-needed                      |
| Red        | `#fee2e2` | `#991b1b` | RAG red, destructive actions, errors, blocks-type edges    |
| Info       | `#e0f2fe` | `#075985` | Informational banners                                      |

Dark-mode status pairs deepen the surface and lighten the text; see §3.5.
Status colour is never the sole signal — pair with an icon or a text label.

### 3.4 Usage rules

- **Deep purple (`--brand`)** leads. It is the default colour of the primary
  button, the page title, and the sidebar.
- **Teal (`--brand-accent`)** is the confirm/approve/success colour and also
  the focus ring. Never use it as body text — the contrast is insufficient at
  small sizes.
- **Orange (`--brand-orange`)** is reserved for secondary attention (graph
  edges, category tags on marketing pages). It is not a warning colour. Use
  amber for warnings.
- **Destructive red** is outside the brand palette for accessibility and
  universal comprehension (`red-600` / `red-700` in Tailwind's default scale).
- **Grey (`--brand-muted`)** is for disabled and inert UI only. For body
  copy, hints, and metadata use the semantic `--text-muted`.

### 3.5 Dark mode

Dark mode is a first-class mode, not an inversion. Rules:

- Surfaces get deeper purple undertone (`#140b1a`, `#1b1124`, `#231530`) rather
  than pure black — this keeps the brand temperature.
- Text is a warm off-white (`#f2ecf2`), never pure white.
- `--brand` stops being the primary button background in dark mode — it is
  replaced by `--brand-accent` (teal) for primary actions, because teal reads
  more cleanly on a purple-black surface than deep purple on deep purple.
- Status surfaces become `~12%` opacity tints of the status hue instead of
  solid pastels; text lightens to the status hue at `~80%` lightness.
- Focus rings, brand accent, and semantic tokens keep the same *names* in both
  modes — only the mapped colour changes.

Dark mode is toggled via `prefers-color-scheme` by default and must also be
manually selectable (`data-theme="dark"` on `<html>`).

---

## 4. Typography

### 4.1 Typeface

**Poppins** (Google Fonts, weights 300 / 400 / 500 / 600 / 700) is the single
UI typeface. It is loaded via `next/font/google` and exposed as
`--font-poppins`.

- Weights used in product UI: **400** (body), **500** (form labels, table
  headers), **600** (headings, button labels, emphasised numerals), **700**
  (sparingly — only for marketing hero).
- Weight 300 is reserved for oversized editorial display on marketing surfaces
  (≥ 40px).
- No italics in UI. Italics are permitted only in long-form written content
  (docs, help pages).

Fallback stack: `ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
'Segoe UI', sans-serif`.

**Monospace:** Geist Mono, for identifiers, hashes, audit events, and any
numeric value where column alignment matters. Always pair numerals with
`tabular-nums` in CSS.

### 4.2 Type scale

| Role                     | Size     | Line height | Weight | Tracking      |
| ------------------------ | -------- | ----------- | ------ | ------------- |
| Display (marketing only) | 48 / 56  | 1.05        | 300–400| `-0.02em`     |
| H1 (page title)          | 28 / 32  | 1.15        | 600    | `-0.01em`     |
| H2 (section)             | 20 / 24  | 1.2         | 600    | `-0.005em`    |
| H3 (card title)          | 18 / 22  | 1.25        | 600    | `0`           |
| Body                     | 14 / 20  | 1.45        | 400    | `0`           |
| Body small               | 13 / 18  | 1.4         | 400    | `0`           |
| Caption / hint           | 12 / 16  | 1.35        | 400    | `0`           |
| Eyebrow (uppercase)      | 11 / 14  | 1.2         | 600    | `0.12em`      |
| Numeric lockup           | Any      | —           | 600    | `tabular-nums`|

**Eyebrow** is the small uppercase tracked label used above H1s and inside
card headers (e.g. `PHASE 3 · FY26`). It is always set in `--brand-accent` or
`--text-muted` — never in body foreground.

### 4.3 Rules

- Maximum body measure: **72ch** for long-form, **52ch** for dense card copy.
- Never set body text smaller than 13px.
- Never mix three weights in one paragraph.
- Headings use sentence case. Eyebrow labels use UPPER CASE with tracked
  spacing (`0.12em`) — the only uppercase in the system.
- Numerals in tables, dashboards, or financial views always use
  `tabular-nums`.

---

## 5. Space, shape, elevation

### 5.1 Spacing scale (4px base)

| Token | Value  | Common use                                       |
| ----- | ------ | ------------------------------------------------ |
| `1`   | 4px    | Icon-to-label gap, tight stacks                  |
| `2`   | 8px    | Inline field gaps, chip padding                  |
| `3`   | 12px   | Default form control internal spacing            |
| `4`   | 16px   | Default gap between siblings                     |
| `6`   | 24px   | Card padding, section padding                    |
| `8`   | 32px   | Page section gaps                                |
| `12`  | 48px   | Page header → content gap                        |
| `16`  | 64px   | Editorial / marketing rhythm                     |

Use the scale. Don't use arbitrary pixel values (`p-[17px]` is a smell).

### 5.2 Radius

| Token | Value | Used on                                            |
| ----- | ----- | -------------------------------------------------- |
| `sm`  | 4px   | Badges, chips, small pills                         |
| `md`  | 6px   | Inputs, buttons, default                           |
| `lg`  | 8px   | Cards, modals, panels                              |
| `xl`  | 12px  | Oversized hero cards, marketing panels             |
| `full`| 9999px| Avatar, status dots, pill tags                     |

Never use raw-square corners in product UI (`radius: 0`). Avoid mixing radii
within a single composition — nested corners should be consistent or step by
one token.

### 5.3 Elevation

Three shadow levels, nothing more:

| Token      | Shadow                                              | Used on                          |
| ---------- | --------------------------------------------------- | -------------------------------- |
| `shadow-sm`| `0 1px 2px rgb(0 0 0 / 0.06)`                       | Buttons, default cards           |
| `shadow`   | `0 4px 12px -2px rgb(0 0 0 / 0.08)`                 | Hover-raised cards, dropdowns    |
| `shadow-lg`| `0 16px 40px -12px rgb(0 0 0 / 0.18)`               | Modals, command palette          |

No glow effects. No coloured shadows. In dark mode, shadows are retained but
softened (`opacity × 0.6`) because the contrast against dark surfaces is less
useful than an explicit border.

### 5.4 Borders

Default `1px` solid, colour `--border`. Emphasised `1px` solid
`--border-strong`. No `2px` borders except around focus states. Do not combine
shadow and border on the same element unless explicitly specified by a
component (cards use border alone in dark mode; border + shadow in light mode).

### 5.5 Grid and layout

- **Content max-width:** 1280px for application views, 1120px for editorial
  views, 640px for marketing read-longform.
- **Page padding:** 24px on mobile, 32px on tablet, 48px on desktop.
- **Columns:** 12-column grid with 24px gutters for desktop; most working
  views use a 2–3 column composition rather than a strict grid.
- **Responsive breakpoints:** `sm 640px`, `md 768px`, `lg 1024px`, `xl 1280px`,
  `2xl 1536px`. Use them sparingly — most working screens collapse to a single
  column below `md` and should not be re-designed below that.

---

## 6. Motion

Motion is short and functional. It should never delay a decision.

- **Duration tokens:** `fast 120ms`, `base 180ms`, `slow 240ms`.
  Hover/state changes use `fast`. Entry/exit of panels and modals use `base`.
  Reserve `slow` for large pieces (drawer slides, route transitions).
- **Easing:** default `cubic-bezier(0.2, 0, 0, 1)` (quick out, calm in) for
  enter/state; `cubic-bezier(0.4, 0, 1, 1)` for exit.
- **Animate:** opacity, transform (translate/scale), colour. Do not animate
  box-shadow or width/height for layout changes — transform only.
- **Reduced motion:** honour `prefers-reduced-motion: reduce`. Replace all
  motion over `base` with an instant transition or a short opacity fade.
- **Never:** bouncing, spring overshoots, decorative loops, page-load
  orchestrated sequences. Motion communicates causality, not personality.

---

## 7. Iconography

- Single icon library per product; **Lucide** is the default (open-source,
  consistent stroke, wide coverage).
- Stroke width: **1.5px** (Lucide default). Do not use filled icons except
  for status dots and avatars.
- Size scale: **14 · 16 · 20 · 24 · 32**. Pick one size per context; don't
  mix.
- Icons are decorative unless labelled. Icon-only buttons require an
  `aria-label` and a visible tooltip on hover/focus.
- Icon colour inherits from surrounding text colour. Tinting an icon with
  `--brand-accent` is permitted for *status* purposes only (e.g. success
  checkmark in a toast).

---

## 8. Components

Each component has a **purpose**, a **spec** (anatomy, sizing, states), and
**usage rules**. When a product needs a new component, start from the rules in
§1 and §2 and mirror the shape of these specs.

### 8.1 Button

**Purpose:** Primary affordance for actions. One primary button per view.

**Variants** (from `components/ui/button.tsx`):

| Variant     | Background             | Text         | Used for                                   |
| ----------- | ---------------------- | ------------ | ------------------------------------------ |
| `primary`   | `--brand`              | `--brand-contrast` | Default action. One per view.       |
| `accent`    | `--brand-accent`       | `--brand-contrast` | Confirm / approve / save.           |
| `secondary` | transparent + `border-brand/20` | `--brand` | Secondary actions, cancel.         |
| `ghost`     | transparent            | `--foreground`     | Dense inline actions, toolbar.      |
| `danger`    | `red-600` → `red-700`  | white        | Destructive (delete, withdraw, etc.).      |

**Sizes:**

| Size | Height | Padding-x | Text size |
| ---- | ------ | --------- | --------- |
| `sm` | 32px   | 12px      | 12px      |
| `md` | 40px   | 16px      | 14px      |
| `lg` | 44px   | 24px      | 14px      |

**States:** default, hover, active, focus-visible (2px teal outline, 2px
offset), disabled (50% opacity, pointer-events none), loading (label replaced
by label + spinner — the button width is locked to prevent jump).

**Rules:**

- Only one `primary` per view. If you need a second emphatic action, it's
  `accent`.
- Button labels are verbs: "Create initiative", "Book value", "Approve".
  Never "OK" or "Submit".
- Never use a `danger` button for a non-destructive action. Never use a
  `primary` button for an irreversible destructive action.
- Icon-only buttons must be `ghost` + `aria-label`.

### 8.2 Input, Textarea, Select

**Purpose:** Text entry and option selection.

**Spec** (from `components/ui/input.tsx`):

- Height: 40px (aligns with `md` button).
- Padding: 12px horizontal, 8px vertical.
- Border: `1px solid --border-strong` on a `--surface` background.
- Focus: border → `--foreground`, `ring 1px --foreground`, outline removed.
  (This differs from the global teal focus ring — for inputs, the ring is
  colour-matched to the border so the field still reads as a field.)
- Placeholder: `--foreground / 40%`.
- Disabled: opacity 50%, no border change.
- Invalid: border `red-600`, hint text replaced by error in `red-600` at
  12px.

**Rules:**

- Inputs live inside a `<Field>` (see §8.3). Never ship a bare input without
  a label.
- Number fields: right-align the value, use `tabular-nums`, show the unit
  inline or in the label (e.g. `Cost (GBP)`).
- Textarea resize: `resize-y` only. Fixed minimum height of 96px.

### 8.3 Field

**Purpose:** Wraps a form control with its label, hint, and error.

**Anatomy:**

```
┌─────────────────────────────────┐
│ Label (14px · 500)    *         │  ← red asterisk if required
│ [ Input / Select / Textarea  ]  │
│ Hint (12px · muted)             │  ← replaced by error when present
└─────────────────────────────────┘
```

**Rules:**

- Every form control has a `Field`. No floating labels. No placeholder-as-
  label.
- Required marker is a red asterisk **after** the label, with a space
  (`Label *`). Never prefix.
- Error replaces hint — never stack both.
- Field-level errors are sentence case, action-oriented ("Enter a date
  after the start date."), under 80 characters.

### 8.4 Card

**Purpose:** Groups a unit of content with its own header, body, and actions.

**Spec** (from `components/ui/card.tsx`):

- Radius: `lg` (8px).
- Padding: 24px (spacing `6`).
- Border: `1px solid --border`.
- Shadow: `shadow-sm` (light mode only).
- Background: `--surface`.

**Subcomponents:** `Card`, `CardHeader`, `CardTitle` (H3 spec), `CardDescription`
(body small, muted).

**Rules:**

- Max two levels of nesting (a card inside a card). Deeper = refactor.
- A card without a title is a panel. Panels use the same spec but omit
  `CardHeader`.
- Cards are never clickable wholesale unless every child element is also
  non-interactive. Prefer a primary action button inside the card.

### 8.5 Navigation

**Top-level workspace nav** (from `app/(authed)/w/[workspaceId]/layout.tsx`):

- Horizontal tab bar below the workspace title.
- Border-bottom on the container, `1px --border`.
- Each item: 12px padding, 500 weight, 14px text, 2px transparent
  bottom-border that becomes `--brand-accent` on hover/active.
- Active tab: `--brand-accent` bottom border, `--brand` text colour.
- No pill/background fill on tabs — the underline carries the state.

**Rules:**

- Max 8 top-level items. If you need more, group into a secondary level.
- Never combine horizontal tabs with a sidebar for the same level of
  navigation. Pick one.
- Breadcrumbs appear above H1 in 12px muted text, separated by `/`.

### 8.6 StageProgress (stepper)

**Purpose:** Shows a linear stage-gate journey (Summit methodology) or any
ordered workflow.

**Spec** (from `components/stage-progress.tsx`):

- Connected pill-row — no gaps between steps.
- States:
  - Complete: `--brand-accent / 10%` background, `--brand` text, accent
    border.
  - Active: solid `--brand` background, white text, `--brand` border.
  - Upcoming: transparent, `--text-muted`, `--border` border.
- Always prefix with the step number (`1. Identify`).

**Rules:**

- Use for linear flows only. For branching workflows use a DependencyGraph
  (§8.8) or a Kanban board.
- If step count > 8, collapse to `Step 3 of 12 · Design` and show the full
  list in a popover.

### 8.7 RAG badge

**Purpose:** Compact status signal for an initiative, risk, or metric.

**Spec:**

- Pill shape, radius `full`, 14px height, 11px bold uppercase text.
- Pairings:
  - Green → `bg #dcfce7`, `text #166534`.
  - Amber → `bg #fef3c7`, `text #92400e`.
  - Red → `bg #fee2e2`, `text #991b1b`.
- Dark mode: surface becomes the corresponding `status-hue / 12%` tint; text
  brightens to `status-hue-400`.
- Always accompanied by a status word (`RED` not just a red dot) — colour
  is never the sole signal.

### 8.8 DependencyGraph

**Purpose:** Visualises typed relationships between initiatives across stages.

**Spec** (from `components/dependency-graph.tsx`):

- Stage-columned SVG. Columns are methodology stages, ordered left to right.
- Node: 220 × 58, radius 6, 4px left-edge RAG bar, name + owner + RAG pill.
- Edge types:
  - `blocks` → solid red (`#c0392b`), arrowhead.
  - `enables` → solid teal (`--brand-accent`), arrowhead.
  - `overlaps` → dashed orange (`--brand-orange`), arrowhead.
- Within a column, nodes sort red → amber → green (at-risk visible first).
- Nodes link to their initiative page via a native `<a>` (SVG-safe).

**Rules:**

- A graph must include a legend when there are ≥ 2 edge types.
- When node count > 40, switch to a dedicated graph page with zoom/pan —
  don't cram.
- Edge labels appear only on hover; never bake them into the edge path.

### 8.9 Components to define when first built

The following components are common across Moorhouse products. They are not
yet implemented in Summit but, when first built, must match these specs.

- **Dialog / Modal.** Centred, max-width 560px (small) or 880px (large),
  radius `lg`, `shadow-lg`, scrim `rgba(20, 11, 26, 0.48)`. Entry via fade +
  8px translate-up over `base` duration.
- **Toast.** Bottom-right on desktop, bottom-centre on mobile. Max width
  360px. Status colour on the 4px left edge. Auto-dismiss 5s (success),
  persistent (error). Never stack more than 3.
- **Empty state.** Icon (32px, muted), H3 heading, one sentence of body, one
  primary CTA. No illustration by default — this is a consulting product,
  not a consumer app. Reserve full illustrations for onboarding only.
- **Data table.** Sticky header row, `--surface-muted` header background,
  `--text-muted` uppercase eyebrow-style column labels, row height 44px
  dense / 56px comfortable, zebra OFF by default, row hover `--brand / 3%`.
  Pagination bottom-right. Column sort icon on hover, persistent when
  active.
- **Tabs (inline).** Same underline-style as top nav but scaled down (10px
  vertical padding, 13px text). Use for secondary navigation inside a page.
- **Dropdown menu.** Radius `md`, `shadow`, padding `1` around, item height
  32px, hover surface `--brand / 5%`, separators `--border`.
- **Tooltip.** 12px text, `--foreground` background, `--background` text,
  radius `sm`, max-width 240px, 6px arrow. Appears after 200ms hover delay.
- **Avatar.** Circle, radius `full`. Sizes 24 / 32 / 40 / 56. Initials in
  Poppins 500, background chosen from a deterministic hash of the name over
  a 6-colour brand-tinted palette.
- **Breadcrumb.** 12px muted text, `/` separators, last item
  `--foreground`.
- **Command palette.** ⌘K / Ctrl-K. 640px wide, vertically centred-upper,
  `shadow-lg`. Input sticks at top, grouped results below with eyebrow
  section headings.

### 8.10 Charts and data viz

Across products, charts follow one house style:

- **Gridlines:** 1px `--border`, horizontal only, never vertical.
- **Axes:** 12px `--text-muted` labels, no axis line (the outermost gridline
  carries it).
- **Series colours (in order):** `--brand`, `--brand-accent`,
  `--brand-orange`, `--brand-ocean`, `--brand-purple`, `--brand-muted`.
  Maximum 6 series per chart — if you need more, rethink the view.
- **Bar chart:** rounded top corners at radius `sm`, 60% category width.
- **Line chart:** 2px stroke, no area fill unless there's a single series.
- **Funnel / waterfall:** brand deep purple for totals, teal for positive
  deltas, red for negative deltas, amber for forecast.
- **Legends:** below the chart on mobile, right on desktop. 12px, 16px
  swatches with 4px radius.
- **Tooltips:** match §8.9 Tooltip; show exact value, `tabular-nums`.
- **Empty state:** Chart area replaced with a 1-line muted hint, never with
  a mock or skeleton that could be mistaken for real data.

---

## 9. Accessibility

Baseline: **WCAG 2.1 AA**. Specific rules:

- **Contrast:** body text ≥ 4.5:1, large text (≥ 18px or 14px bold) ≥ 3:1,
  UI components ≥ 3:1. The brand palette has been selected to meet these —
  `--brand-muted` is *not* a text colour; use `--text-muted` for body.
- **Keyboard:** every interactive element reachable by Tab; focus visible
  via the global teal focus ring (never remove `:focus-visible`). Support
  Escape to dismiss modals and menus; Arrow keys within menus, tabs, and
  radio groups.
- **Screen readers:** use semantic HTML first (`<button>`, `<nav>`,
  `<main>`). Add ARIA only when semantics are insufficient.
  Icon-only buttons require `aria-label`. Decorative icons get
  `aria-hidden="true"`.
- **Motion:** honour `prefers-reduced-motion: reduce` (see §6).
- **Forms:** every input has a visible label (no placeholder-as-label);
  error messages are programmatically associated via `aria-describedby`;
  required fields marked both visually (red asterisk) and programmatically
  (`required` attribute).
- **Colour independence:** every RAG status, error, and warning carries an
  icon or text label in addition to colour.
- **Zoom:** layouts reflow cleanly at 200% zoom without horizontal scrolling
  below `lg` breakpoint.

---

## 10. Code integration

### 10.1 Tokens in Tailwind 4

Tokens are defined in `app/globals.css` under `@theme inline` and exposed as
Tailwind utilities automatically:

- `bg-brand`, `text-brand`, `border-brand` → `--brand`
- `bg-brand-accent`, `text-brand-accent` → `--brand-accent`
- `bg-brand-orange`, `text-brand-orange` → `--brand-orange`
- `bg-background`, `text-foreground` → semantic
- `font-sans` → Poppins stack
- `font-mono` → Geist Mono stack

Extend with opacity modifiers, not new tokens: `bg-brand/5`, `border-brand/10`,
`text-brand/80`.

### 10.2 Component packaging

For Summit today, components live under `components/ui/*.tsx` and
`components/brand/logo.tsx`. For multi-product reuse, the target is a shared
package `@moorhouse/ui` that ships:

- `tokens.css` — `:root` and `@theme inline` definitions.
- `components/*` — the components specified in §8.
- `fonts.ts` — the Poppins + Geist Mono loaders.
- `icons.ts` — a curated re-export of the Lucide set actually used.
- `BrandLogo` — the firm mark component.

Until that package exists, new products should copy `components/ui/*`
verbatim rather than fork the visuals.

### 10.3 Do / Don't quick reference

**Do:**

- Use tokens, not raw hex.
- Keep one primary action per view.
- Use the spacing scale — no arbitrary pixel values.
- Let typography and whitespace carry hierarchy before colour.
- Pair colour with icon/text for every status.
- Test every new screen at 200% zoom and with keyboard only.

**Don't:**

- Use gradients, glassmorphism, coloured shadows, or decorative drop-shadows.
- Use emoji or exclamation marks in UI microcopy.
- Put body text on `--brand-muted` or `--brand-accent`.
- Mix three font weights in a paragraph.
- Animate layout (width/height) or use spring/bounce easing.
- Invent new radii, shadows, or colour tints outside the token system.
- Use `danger` buttons for non-destructive actions.
- Ship a form control without a `<Field>` wrapper.

---

## 11. Change control

This document is versioned. Breaking changes (token rename, component
removal, palette shift) require:

1. An entry in the changelog below with rationale.
2. A version bump (major for breaking, minor for additions, patch for
   clarifications).
3. A migration note describing how to update existing Moorhouse products.

### Changelog

| Version | Date       | Notes                                               |
| ------- | ---------- | --------------------------------------------------- |
| 1.0     | 2026-04-24 | Initial standard, codified from Summit MVP.         |

---

## 12. Open items

Placeholders to fill in as the standard matures:

- **§2.2 Tone of voice** — insert full Moorhouse Tone of Voice Guide.
- **§8.9 new components** — promote each into a full spec (with code
  reference) when first built.
- **§10.2 packaging** — extract `@moorhouse/ui` shared package when the
  second Moorhouse product begins.
- **Illustration system** — onboarding illustration style (line weight,
  palette usage, composition) to be defined when onboarding flows exist.
- **Motion library** — canonical enter/exit animations as React hooks when
  the component count justifies it.
