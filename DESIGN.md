---
name: banco-motos
description: Painel de instrumentos que trata roteiros e vídeos coletados sobre moto elétrica como leituras de um dashboard, não como um feed de cards.
colors:
  ground: "#0b0d0c"
  panel: "#141715"
  panel-raised: "#191d1a"
  rim: "#3a3f3c"
  rim-dim: "#242624"
  ink: "#e9ece9"
  ink-dim: "#9aa19c"
  amber: "#e08d3d"
  amber-dim: "#c9975a"
  teal: "#4fa89b"
  teal-dim: "#2c5750"
typography:
  label:
    fontFamily: "ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace"
    fontSize: "0.62rem"
    fontWeight: 400
    lineHeight: 1.2
    letterSpacing: "0.08em"
  numeral:
    fontFamily: "ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace"
    fontSize: "0.72rem–0.8rem"
    fontWeight: 400
    lineHeight: 1.2
    letterSpacing: "normal"
  body:
    fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
    fontSize: "0.82rem–0.9rem"
    fontWeight: 400
    lineHeight: 1.35
  wordmark:
    fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
    fontSize: "1.05rem"
    fontWeight: 700
    letterSpacing: "0.02em"
rounded:
  sm: "3px"
  md: "4px"
spacing:
  xs: "0.35rem"
  sm: "0.6rem"
  md: "0.75rem"
  lg: "1rem"
components:
  gauge-label:
    textColor: "{colors.amber-dim}"
    typography: "{typography.label}"
  gauge-value:
    textColor: "{colors.ink}"
    typography: "{typography.body}"
  tile:
    backgroundColor: "{colors.panel}"
    rounded: "{rounded.md}"
  trip-toggle:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink-dim}"
    rounded: "{rounded.sm}"
    padding: "0.4rem 0.65rem"
  chip-active:
    backgroundColor: "{colors.amber}"
    textColor: "{colors.ground}"
    rounded: "{rounded.sm}"
---

# Design System: banco-motos

## Overview

**Creative North Star: "The Electric-Moto Instrument Cluster"**

banco-motos reads its daily haul of scraped videos and generated roteiros the way a moto elétrica's dashboard reads speed, charge, and regen state: as a bank of equal-weight instrument tiles, not a scrolling social feed. The subject of the product (moto elétrica) supplies its own visual language, so the panel borrows the discipline of a real instrument cluster — near-black body, one warm signal accent used sparingly, tabular numerals that don't jiggle, thin rules only where a gauge boundary actually exists. There is no glow, no bloom, no decorative color; precision over mood is the whole point, because the user scans this one-handed on a phone right after a push notification.

The palette is intentionally restrained to two functional colors on a near-black ground: amber for the single most important signal per surface (state, active filter, active focus, hover-affordance) and teal reserved exclusively for the "pronto" state light. Every other value on the page is neutral ink or dim ink — there is no rainbow of platform colors, no rotating accent per tile.

**Key Characteristics:**
- Near-black instrument body with two functional accent colors, never decorative color
- Monospace numerals and labels for anything gauge-like (counts, dates, times, labels); system sans for prose (roteiro body, wordmark)
- Flat surfaces separated by 1px rules that mark real instrument-panel boundaries, not shadows
- Equal-weight three-gauge triad per tile: no gauge outranks another visually

## Colors

Two functional accents on a near-black instrument body; everything else is neutral ink at two levels of dimness.

### Primary
- **Amber signal** (`#e08d3d`): the single most important accent, used for the top strip's underline, the wordmark's separator glyph, active/hover states on interactive controls (trip-toggle, chip, source link), and the active-filter chip fill. Never used decoratively or repeated per-item.
- **Amber-dim** (`#c9975a`): a legibility-corrected variant of amber, used for gauge labels (small uppercase mono text) where full-saturation amber failed contrast against the panel background.

### Secondary
- **Teal signal** (`#4fa89b`): reserved exclusively for the tile state light. It marks a "pronto" record — every record shown has already succeeded through the pipeline (failed/skipped items never reach storage), so teal is the only state color the build actually needs; there is no red/amber/gray state-light variant to document because none is representable by the data.

### Neutral
- **Ground** (`#0b0d0c`): page background, the instrument body itself.
- **Panel** (`#141715`): tile background, one step up from ground.
- **Panel-raised** (`#191d1a`): the source-swatch glyph box and the expand-button footer, one step up from panel.
- **Rim** (`#3a3f3c`): border on the source-swatch glyph box, the one slightly brighter structural border in the system.
- **Rim-dim** (`#242624`): the default hairline rule color — tile borders, gauge dividers, trip-computer/search borders, expand-button top border.
- **Ink** (`#e9ece9`): primary text — gauge values, roteiro body, wordmark.
- **Ink-dim** (`#9aa19c`): secondary text — platform label, timestamps, gauge sub-values, placeholder text, inactive chip/toggle text.

### Named Rules
**The Two-Signal Rule.** Only two colors carry meaning: amber for the single most important accent, teal for the one binary state the data can represent. Every other color on the page is neutral. A third functional color is not added without a third distinct state to represent.

**The Rarity Rule.** Amber never repeats per-tile as a decorative habit — it marks the top strip's boundary once, and otherwise only appears on interactive/active states. It does not recolor every label or icon.

## Typography

**Body Font:** system-ui, -apple-system, "Segoe UI", Roboto, sans-serif
**Label/Mono Font:** ui-monospace, "SFMono-Regular", Consolas, "Liberation Mono", monospace

**Character:** A workhorse sans for prose that gets out of the way (roteiro text, wordmark), paired with a tabular monospace for anything a real gauge would render as a stable readout — counts, dates, times, uppercase labels — so digits never jiggle between renders.

### Hierarchy
- **Wordmark** (700, 1.05rem, sans): the "banco-motos" title in the sticky top strip; the amber hyphen is the only mid-word color break in the system.
- **Readout** (400, 0.8rem, mono, tabular-nums): the item-count + date readout in the top strip and the timestamp on each tile head.
- **Label** (400, 0.62–0.72rem, mono, uppercase, 0.04–0.08em tracking): gauge labels, platform label, chip text, trip-toggle text, expand-button text — all structural/UI labels are monospace uppercase, never sans.
- **Value** (400, 0.82–0.9rem, sans): gauge readout body (tema/gancho/formato text, roteiro excerpt), the primary reading content of a tile.
- **Value-sub** (400, 0.74rem, sans, dim): secondary line inside a gauge (e.g. supporting detail under the primary reading).

### Named Rules
**The Numeral Discipline Rule.** Any value that is a count, date, or timestamp renders in the monospace stack with tabular figures — never in the sans body font. Prose content (tema, gancho, roteiro text) always renders in sans, never in mono.

## Layout

Single-column tile bank, mobile-first at 390px, capped and centered on desktop. A sticky top instrument strip (wordmark + readout) stays pinned above a collapsible trip-computer search/filter row (icon-button collapsed by default, expands to a search field + platform chip row on tap) — the two together form the panel's control head, so the tile bank starts immediately below. Tiles stack vertically with 0.75rem gap; each tile's body is a three-column equal-width gauge grid (`grid-template-columns: repeat(3, 1fr)`) separated by 1px rim-dim hairlines, so all three readings (tema/gancho/formato · vídeo-fonte · roteiro) carry identical visual weight — no gauge is emphasized over another. At ≥720px the strip, trip-computer, and tile bank gain 2rem side padding and the tile bank caps at 68rem, centered.

## Elevation & Depth

Flat. There are no shadows anywhere in the stylesheet. Depth is conveyed entirely through tonal layering on a near-black scale (ground → panel → panel-raised) and 1px hairline rules (rim-dim, rim) that mark real structural boundaries — a gauge edge, a tile edge, a control's border — never a decorative container. This is a deliberate instrument-panel choice: the OWN-WORLD contract calls for "no glow/bloom blur — precision over mood," and the build has no glow, blur, or offset-shadow anywhere.

### Named Rules
**The No-Glow Rule.** Depth comes from flat tonal steps and 1px rules only. No box-shadow, no blur, no glow is used anywhere, including on hover/active states (which shift color, not elevation).

## Shapes

Small, consistent corner radii throughout: 3px on interactive controls (trip-toggle, chips, inputs, source-swatch glyph), 4px on tiles. No large radii, no fully rounded (pill) shapes anywhere, and no sharp/zero-radius edges either — the form language sits deliberately between neobrutalist-sharp and app-rounded, reading as machined rather than soft. Borders are always 1px hairlines in rim or rim-dim; there is no border-width variation.

## Components

### Top Strip (signature component)
- **Style:** sticky header, ground background, 1px solid amber bottom border (the only full-width amber rule on the page).
- **Content:** wordmark left (sans, bold, amber hyphen accent), tabular-mono readout right (item count + date).

### Trip Computer (signature component)
- **Style:** collapsible search/filter row below the top strip, styled as a sub-panel: a mono uppercase icon-button toggle (`buscar / filtrar`) that expands to a search input and a platform chip group. Collapsed by default so it never competes with the tile bank for first-viewport space.
- **Chips:** rim-dim border, panel background, ink-dim text at rest; active chip inverts to amber fill with ground text (`aria-pressed="true"`).
- **Toggle/hover:** text and border shift to amber/amber-dim on hover or when expanded; no background change.

### Tiles / Gauge Triad (signature component)
- **Corner Style:** 4px radius, 1px rim-dim border, panel background.
- **Head:** platform shown as a plain mono uppercase text label (no color-coded dot — platform never carries color meaning), a tabular-mono timestamp, and the teal state-light dot in the top-right corner (the page's only teal usage).
- **Body:** three equal-width gauges (tema/gancho/formato · vídeo-fonte · roteiro) separated by 1px rim-dim gridlines. Each gauge has an amber-dim mono uppercase label, then ink-colored sans value text (line-clamped to 3 lines), with an optional ink-dim sub-value (clamped to 2 lines).
- **Vídeo-fonte gauge:** carries a bordered-square swatch (1.7rem, rim border, panel-raised background, 3px radius) showing the platform's initials in mono bold, next to a mono underlined source link that turns amber on hover.
- **Expand:** a full-width footer button (panel-raised, mono uppercase, ink-dim, amber on hover/open) toggles the roteiro body inline below the triad — no modal, no navigation away from the bank.

### Inputs / Fields
- **Style:** panel background, 1px rim-dim border, 3px radius, sans text, ink-dim placeholder.
- **Focus/Error:** no focus-ring or error treatment observed in the build; not documented until implemented.

## Do's and Don'ts

### Do:
- **Do** keep amber and teal as the only two functional colors; every other value is neutral ink or panel/ground tone.
- **Do** render counts, dates, and timestamps in the monospace stack with tabular figures; render prose (tema, gancho, roteiro) in sans.
- **Do** use flat tonal layering (ground → panel → panel-raised) and 1px rim rules for depth and structure — never a shadow.
- **Do** keep the three-gauge triad equal-width and equal-weight; no gauge visually outranks another.
- **Do** keep platform identity as a plain text label, never a color-coded dot — color is reserved for the amber/teal signal roles, not for categorical/identity data.

### Don't:
- **Don't** add glow, blur, or box-shadow anywhere, including on hover/active states — depth is tonal and rule-based only, per the OWN-WORLD "precision over mood" contract.
- **Don't** add a third functional color without a third distinct state to represent; teal exists only because "pronto" is the sole state the stored data can carry.
- **Don't** decorate with amber — it marks the single most important signal per surface, not a repeating accent per item.
- **Don't** use pill (fully rounded) shapes or sharp zero-radius edges — the system's radius vocabulary is 3px (controls) and 4px (tiles) only.
