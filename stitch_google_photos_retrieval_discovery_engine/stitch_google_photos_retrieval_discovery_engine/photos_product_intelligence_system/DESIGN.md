---
name: Photos Product Intelligence System
colors:
  surface: '#f7f9ff'
  surface-dim: '#d7dae0'
  surface-bright: '#f7f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f1f4fa'
  surface-container: '#ebeef4'
  surface-container-high: '#e5e8ee'
  surface-container-highest: '#dfe3e8'
  on-surface: '#181c20'
  on-surface-variant: '#414754'
  inverse-surface: '#2d3135'
  inverse-on-surface: '#eef1f7'
  outline: '#727785'
  outline-variant: '#c1c6d6'
  surface-tint: '#005bc0'
  primary: '#005bbf'
  on-primary: '#ffffff'
  primary-container: '#1a73e8'
  on-primary-container: '#ffffff'
  inverse-primary: '#adc7ff'
  secondary: '#006e2c'
  on-secondary: '#ffffff'
  secondary-container: '#86f898'
  on-secondary-container: '#00722f'
  tertiary: '#b81d17'
  on-tertiary: '#ffffff'
  tertiary-container: '#dc392c'
  on-tertiary-container: '#ffffff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d8e2ff'
  primary-fixed-dim: '#adc7ff'
  on-primary-fixed: '#001a41'
  on-primary-fixed-variant: '#004493'
  secondary-fixed: '#89fa9b'
  secondary-fixed-dim: '#6ddd81'
  on-secondary-fixed: '#002108'
  on-secondary-fixed-variant: '#005320'
  tertiary-fixed: '#ffdad5'
  tertiary-fixed-dim: '#ffb4a9'
  on-tertiary-fixed: '#410001'
  on-tertiary-fixed-variant: '#930004'
  background: '#f7f9ff'
  on-background: '#181c20'
  surface-variant: '#dfe3e8'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Inter
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.005em
  title-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0em
  body-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
    letterSpacing: 0em
  body-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: 0.005em
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.03em
  data-tabular:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0em
  code-badge:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.04em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-compact: 0.5rem
  margin: 1.5rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1rem
  space-xl: 1.5rem
---

## Brand & Style

This design system establishes a high-utility, evidence-driven workspace designed for product managers, user researchers, and engineers working on large-scale consumer photo and video products. The visual language blends the rigorous, functional clarity of Google Material 3 with high-density data visualization techniques required for telemetry review, customer sentiment analysis, and comparative research.

The aesthetic philosophy centers on utility-first neutrality:
- **Tone:** Methodical, objective, authoritative, and unobtrusive. The interface recedes entirely to let qualitative user quotes, telemetry graphs, and cohort feedback take visual precedence.
- **Style Archetype:** Corporate / Modern with disciplined Material 3 influences. Structural elevation is achieved via crisp 1px borders and subtle ambient drop shadows rather than stacked planes or colorful fills.
- **Accents:** The iconic 4-color product identity (Google Blue `#1A73E8`, Red `#EA4335`, Yellow `#FBBC04`, Green `#34A853`) is used strictly in functional contexts—such as source tagging, confidence scores, and status flags—never as broad decorative washes or hero gradients.
- **Data Integrity:** Explicit visual signposts, such as high-visibility demo indicators and cohort metadata tags, guarantee that analysts immediately distinguish verified prod telemetry from synthetic test benches.

## Colors

The palette employs a crisp, slate-tinged neutral foundation calibrated for extended desktop analysis sessions, offset by standard Google system primaries and disciplined semantic anchors.

### Surface and Structure
- **Canvas Base (`#F8F9FA`):** The primary off-white backdrop across viewports and drawer scuffs.
- **Surface Elevation (`#FFFFFF`):** Workcards, side inspectors, split-sheets, and table rows.
- **Hairline Dividers (`#DADCE0`):** Outer structural framing, global header separators, and drawer dividers.
- **Subtle Row Borders (`#E0E2E6`):** Secondary containment lines for data tables, inline chips, and sub-card divisions.

### Core Brand & Semantic Colors
- **Primary Blue (`#1A73E8`):** Navigation active states, interactive controls, focused rows, and dominant actions.
- **Success / Healthy Green (`#34A853`):** High confidence intervals, positive sentiment shifts, validated hypotheses, and App Store badges.
- **Warning / Pending Yellow (`#FBBC04`):** Telemetry drift, low sample sizes, needs triage, and unverified data pools.
- **Critical / Blocked Red (`#EA4335`):** Crash rate regressions, negative sentiment anomalies, and critical friction tags.

### Source Taxonomy & Indicators
- **Google Play:** Blue fill tint (`#E8F0FE`) with `#1A73E8` label.
- **App Store:** Dark slate tint (`#F1F3F4`) with `#3C4043` label.
- **Reddit:** Deep orange-red tint (`#FCE8E6`) with `#D93025` label.
- **Community Forums / Web:** Green tint (`#E6F4EA`) with `#137333` label.
- **YouTube:** Soft red outline with `#C5221F` icon accents.
- **DEMO DATA Pill:** Bold solid slate amber (`#FEF7E0`) background paired with `#B06000` text and a 1px border (`#F9AB00`) to prevent data confusion.

## Typography

The type scale prioritizes legibility across complex datasets, structured research transcripts, and analytics dashboards.

- **Primary Typeface (Inter):** Serves for all user interface structures, editorial transcripts, cards, and headings. Features subtle ink-traps and exceptional rendering at micro-scales (11px–13px). Tabular numbers (`tnum`) and slashed zeros (`zero`) must be toggled on across all statistical tables and metrics rows.
- **Data & Label Monospace (JetBrains Mono):** Dedicated to technical metadata, event signatures, user IDs, sample sizes (`n=1,420`), session timestamps, and code snippets.
- **Hierarchy Rules:** 
  - Standard headers use constrained line-heights to support tight density.
  - Section dividers use uppercase, muted micro-labels with enhanced tracking (`0.04em`).
  - Mobile viewports step down `headline-lg` to 22px / 28px line-height to eliminate unnatural breaks in deep analytical headers.

## Layout & Spacing

The layout is built around a dense 8-point base grid (with a strict 4-point micro subgrid) optimized for standard widescreen internal monitors (1440px to 1920px display profiles).

### Workbench Layout Architecture
- **Global Header:** 48px fixed height containing product identification, cohort picker, search input, and system-wide state badges.
- **Left Navigation Rail:** Collapsible width (56px collapsed to 224px expanded) anchored with 1px border right `#DADCE0`.
- **Primary Data View:** Fluid multi-column data workspace with `gutter` spacing at 16px. In dense evidence inspection modes, table gutters collapse to `gutter-compact` (8px).
- **Inspection Drawer (Right Panel):** 440px fixed width slide-over with a 0px left offset against the workbench container, retaining scroll independence.
- **Mobile Adaptations:** Under 768px, navigation collapses into a bottom app bar, drawers convert to full-bleed modal sheets, and horizontal padding drops to `margin-mobile` (16px).

## Elevation & Depth

To maintain high data clarity without optical fatigue, this design system minimizes heavy dropped shadows. Depth is achieved via two primary mechanisms: **Tonal Tiering** and **Boundary Outlines**.

- **Level 0 (Flat / Canvas):** Applied to the foundation background (`#F8F9FA`). No shadow. Separated via explicit 1px borders (`#DADCE0`).
- **Level 1 (Card Rest / Default Sheet):** Used for analytical cards, evidence snippets, and filter bars. 
  - Visual formula: `box-shadow: 0px 1px 2px rgba(60, 64, 67, 0.12), 0px 1px 3px rgba(60, 64, 67, 0.08); border: 1px solid #DADCE0;`
- **Level 2 (Active Drag / Floating Context Filter):** Applied to floating toolbars, contextual action bars, and table column reordering.
  - Visual formula: `box-shadow: 0px 2px 6px 2px rgba(60, 64, 67, 0.15); border: 1px solid #DADCE0;`
- **Level 3 (Modal / Persistent Detail Drawer):** Applied to sliding drill-down panels and confirmation dialogs.
  - Visual formula: `box-shadow: -4px 0px 16px rgba(60, 64, 67, 0.12);` against side content.

## Shapes

The interface embraces a functional, structured geometry that reinforces precision and density.

- **Base Radius (0.25rem / 4px):** Applied to buttons, data cells, tabular inputs, and internal segmented controls.
- **Medium Radius (0.5rem / 8px):** Applied to workbench cards, insight modules, research summary panels, and modal containers.
- **Full Pill Radius (9999px):** Applied selectively to status chips, sentiment ratings, research source identifiers, and global alerts (such as `DEMO DATA`).
- **Sharp Rule Exceptions:** Border-attached side drawers, docked split panes, and header rails maintain squared edges (`0px`) at attachment borders to visually unify with the browser frame.

## Components

### Buttons
- **Primary:** Solid `#1A73E8` fill, `#FFFFFF` text, 4px border radius, 32px height in standard density. Hover state: `#155724` or `#1765CC` with slight ambient shadow.
- **Secondary / Outlined:** `#FFFFFF` fill with 1px border `#DADCE0`, `#3C4043` text. Hover state: `#F1F3F4` fill.
- **Subtle / Ghost:** Transparent fill, `#5F6368` icon or label, 4px corner radius. Used for inline table actions.

### Badges & Pill Chips
- **Data Source Chips:** 22px total height, full pill shape (`9999px`), 8px horizontal padding. Icons sized to 12px inline.
  - *Google Play:* `#E8F0FE` background, `#1967D2` text, no border.
  - *App Store:* `#F1F3F4` background, `#3C4043` text, no border.
  - *Reddit:* `#FCE8E6` background, `#C5221F` text, no border.
  - *Community Forums:* `#E6F4EA` background, `#137333` text, no border.
- **DEMO DATA Badge:** Distinctive 20px height pill, `#FEF7E0` background, `#B06000` text, bordered by `1px solid #F9AB00`. Text formatted in `JetBrains Mono` at 10px uppercase with `0.08em` tracking.

### Research Data Table
- **Header:** Sticky positioning, 36px height, uppercase `11px` typography with `#5F6368` text color, background `#F8F9FA`, bottom border `1px solid #DADCE0`.
- **Row:** 44px standard height (compact mode: 32px), background `#FFFFFF`, bottom border `1px solid #E0E2E6`.
- **States:** Hover row shifts to `#F8F9FA`. Selected state uses `#E8F0FE` fill with a `2px solid #1A73E8` left border highlight.
- **Figures:** All numeric columns (feedback count, sentiment delta, cohort sizes) strictly align right and render in `data-tabular`.

### Evidence Card
- Multi-channel insight presentation container.
- Structured with an elevated white base (`#FFFFFF`), `1px solid #DADCE0` perimeter, 8px corner radius, and 16px internal padding.
- Top meta row holds the source pill, user timestamp, and sentiment polarity chip.
- Middle block contains the verbatim quote (Inter 13px, `#202124` text, 20px line-height) with optional search term highlight overlays (`#FFF0A6`).
- Bottom row displays session telemetry context tags (e.g., `App Version: 6.74.0`, `OS: Android 14`, `Device: Pixel 8 Pro`).

### Side Inspection Drawer
- Slide-over panel docked to the right edge with a fixed 440px width.
- Anchored with a 1px solid `#DADCE0` left border and Level 3 drop shadow.
- Separated into three distinct vertical zones:
  1. Sticky top title bar with record navigation (previous/next entry), source icon, and close control.
  2. Scrollable body with collapsible accordions for raw telemetry, translation diffs, and context screenshots.
  3. Pinned bottom toolbar for Jira/Buganizer dispatch, analyst tagging, and research notes.

### Input Fields & Controls
- **Search Bar:** 36px height, `#F1F3F4` fill, zero outline border at rest. On focus: transitions to `#FFFFFF`, `2px solid #1A73E8`, and drops a Level 1 shadow. Integrated keyboard shortcut visual tag (`/` or `⌘K`) set in `JetBrains Mono`.
- **Checkboxes & Radios:** Scaled to 16px. Checked state employs `#1A73E8` fill with crisp white checkmark glyph. Unchecked state uses 1.5px border `#5F6368`.