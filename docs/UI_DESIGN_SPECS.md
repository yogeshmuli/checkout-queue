# UI Design Specs

Derived from the provided QuT reference screenshot.

## Brand Impression

The UI should feel retail-premium, fast, clean, and energetic. Use a red-first brand system with deep navy typography, white surfaces, pale blush backgrounds, and rounded high-comfort controls.

## Color Palette

| Token | Hex | Usage |
| --- | --- | --- |
| `brand-red` | `#FF3833` | Primary navigation, primary buttons, active brand accents |
| `brand-red-deep` | `#E5222A` | Button hover, strong headings, destructive emphasis where appropriate |
| `brand-red-dark` | `#B91C1C` | Pressed state and deep red accents |
| `brand-soft` | `#FFE1E1` | Soft borders, focus rings, light chips |
| `brand-blush` | `#FFF5F5` | Page background panels and hero-like surfaces |
| `ink` | `#101828` | Main headings and high-emphasis text |
| `charcoal` | `#344054` | Body text |
| `muted` | `#667085` | Supporting labels and secondary text |
| `line` | `#EAECF0` | Borders and separators |
| `success` | `#16A34A` | Positive status only |
| `warning` | `#D97706` | Warning status only |

## Typography

Primary font:

```text
Poppins
```

Fallback:

```text
Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif
```

Guidelines:

- Headings use `Poppins`, heavy weights from `700` to `900`.
- Body copy uses the same stack at `400` to `500`.
- Hero and large dashboard numbers should feel bold and rounded.
- Letter spacing stays normal except small uppercase labels, which may use slight positive tracking.

## Shape And Elevation

- Cards use `12px` radius for primary surfaces.
- Inputs and buttons use `999px` for pill actions or `12px` for compact operational controls.
- Shadows are soft and warm, similar to:

```text
0 18px 45px rgba(16, 24, 40, 0.10)
```

## Component Rules

- Primary actions are red with white text.
- Secondary actions are white with soft red or neutral borders.
- Active navigation uses a white pill on red navigation bars or a blush pill in sidebars.
- Customer-facing pages should use a red-to-blush brand background instead of green.
- Success green is reserved for actual status such as optimized, active, or completed.

