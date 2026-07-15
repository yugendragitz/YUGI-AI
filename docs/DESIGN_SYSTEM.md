# YUGI-AI Design System

> **Version**: 1.0.0
> **Status**: Active — All modules MUST conform to this system.
> **Last Updated**: 2026-07-15
> **Owner**: UI/UX Designer + Frontend Engineering

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [Color Palette](#2-color-palette)
3. [Typography](#3-typography)
4. [Spacing](#4-spacing)
5. [Border Radius](#5-border-radius)
6. [Shadows & Elevation](#6-shadows--elevation)
7. [Glassmorphism](#7-glassmorphism)
8. [Animations & Motion Principles](#8-animations--motion-principles)
9. [3D Guidelines](#9-3d-guidelines)
10. [Iconography](#10-iconography)
11. [Component Naming Convention](#11-component-naming-convention)
12. [Responsive Breakpoints](#12-responsive-breakpoints)
13. [Accessibility](#13-accessibility)
14. [Dark Theme Specification](#14-dark-theme-specification)
15. [Sound Design](#15-sound-design)

---

## 1. Design Philosophy

### Core Principles

| Principle | Description |
|-----------|-------------|
| **Neural Elegance** | Every element should feel like it belongs inside an intelligent operating system. No generic web app patterns. |
| **Depth Through Light** | Use light as information — glows indicate activity, dim means dormant, pulsing means processing. |
| **Quiet Confidence** | Premium feels restrained, not loud. Subtle gradients over hard borders. Soft glows over harsh shadows. |
| **Responsive Intelligence** | The interface should feel alive — elements react to hover, focus, and state changes with purposeful animations. |
| **Zero Clutter** | Every pixel earns its place. If it doesn't serve the user, it doesn't exist. |

### Visual Inspirations

| Source | What We Take |
|--------|-------------|
| **Apple Vision Pro** | Spatial depth, frosted glass panels, subtle parallax, typography hierarchy |
| **Iron Man HUD** | Information density in glass overlays, accent glows on active elements |
| **Nothing OS** | Dot-matrix aesthetics for loading states, minimal iconography, bold typography |
| **Tesla UI** | Full-bleed dark canvas, clean data visualization, functional minimalism |
| **Interstellar** | Deep space color palette, wormhole-inspired particle effects, cosmic scale |
| **Cyberpunk** | Neon accent lines, cyan/magenta highlights, futuristic data grids |

---

## 2. Color Palette

### Primary Backgrounds

```css
--color-bg-void:        hsl(225, 30%, 3%);     /* Deepest background — the void */
--color-bg-primary:     hsl(225, 25%, 6%);     /* Primary background */
--color-bg-secondary:   hsl(225, 20%, 10%);    /* Secondary panels */
--color-bg-elevated:    hsl(225, 18%, 14%);    /* Cards, modals, elevated surfaces */
--color-bg-hover:       hsl(225, 16%, 18%);    /* Hover states on backgrounds */
```

### Accent Colors

```css
/* YUGI Signature Blue — Primary interactive color */
--color-accent-primary:     hsl(210, 100%, 60%);
--color-accent-primary-dim: hsl(210, 80%, 45%);
--color-accent-primary-bright: hsl(210, 100%, 72%);

/* Violet — Secondary accent, used for AI-related elements */
--color-accent-secondary:     hsl(275, 80%, 65%);
--color-accent-secondary-dim: hsl(275, 60%, 50%);

/* Cyan — Cyberpunk accent, used for data/metrics */
--color-accent-cyan:     hsl(185, 100%, 55%);
--color-accent-cyan-dim: hsl(185, 80%, 40%);

/* Gradient — Primary brand gradient */
--gradient-brand: linear-gradient(135deg, hsl(210, 100%, 60%), hsl(275, 80%, 65%));
--gradient-brand-hover: linear-gradient(135deg, hsl(210, 100%, 68%), hsl(275, 80%, 72%));

/* Gradient — Neon edge glow */
--gradient-neon: linear-gradient(90deg, hsl(210, 100%, 60%), hsl(185, 100%, 55%));
```

### Semantic Colors

```css
--color-success:         hsl(145, 70%, 50%);
--color-success-dim:     hsl(145, 50%, 35%);
--color-success-bg:      hsla(145, 70%, 50%, 0.1);

--color-warning:         hsl(35, 95%, 55%);
--color-warning-dim:     hsl(35, 75%, 40%);
--color-warning-bg:      hsla(35, 95%, 55%, 0.1);

--color-error:           hsl(0, 75%, 55%);
--color-error-dim:       hsl(0, 55%, 40%);
--color-error-bg:        hsla(0, 75%, 55%, 0.1);

--color-info:            hsl(210, 100%, 60%);
--color-info-bg:         hsla(210, 100%, 60%, 0.1);
```

### Text Colors

```css
--color-text-primary:    hsl(0, 0%, 95%);      /* Primary content */
--color-text-secondary:  hsl(225, 15%, 55%);   /* Labels, descriptions */
--color-text-tertiary:   hsl(225, 12%, 38%);   /* Placeholders, disabled */
--color-text-inverse:    hsl(225, 25%, 6%);    /* Text on light backgrounds */
--color-text-accent:     hsl(210, 100%, 68%);  /* Links, interactive text */
```

### Border Colors

```css
--color-border-default:  hsla(0, 0%, 100%, 0.06);   /* Default borders */
--color-border-hover:    hsla(0, 0%, 100%, 0.12);   /* Hover state borders */
--color-border-focus:    hsl(210, 100%, 60%);       /* Focus rings */
--color-border-glow:     hsla(210, 100%, 60%, 0.3); /* Glow borders */
```

### Usage Rules

> **NEVER** use raw color values in components. Always reference design tokens.
> **NEVER** use pure black (`#000`) or pure white (`#fff`) — always use the palette.
> **NEVER** mix warm and cool grays — all grays use the 225° hue base.

---

## 3. Typography

### Font Stack

```css
--font-primary:   'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-mono:      'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
```

> Load from Google Fonts: `Inter:wght@300;400;500;600;700` and `JetBrains Mono:wght@400;500;600`

### Type Scale

| Token | Size | Weight | Line Height | Letter Spacing | Usage |
|-------|------|--------|-------------|----------------|-------|
| `--text-display` | 64px | 700 | 1.1 | -0.03em | Hero headlines |
| `--text-h1` | 48px | 700 | 1.15 | -0.025em | Page titles |
| `--text-h2` | 32px | 600 | 1.2 | -0.02em | Section headers |
| `--text-h3` | 24px | 600 | 1.3 | -0.015em | Card titles |
| `--text-h4` | 20px | 600 | 1.35 | -0.01em | Subsection headers |
| `--text-body-lg` | 18px | 400 | 1.6 | 0 | Large body text |
| `--text-body` | 16px | 400 | 1.6 | 0 | Default body text |
| `--text-body-sm` | 14px | 400 | 1.5 | 0.005em | Secondary text |
| `--text-caption` | 12px | 500 | 1.4 | 0.01em | Captions, labels |
| `--text-overline` | 11px | 600 | 1.2 | 0.08em | Overlines (UPPERCASE) |
| `--text-code` | 14px | 400 | 1.6 | 0 | Code blocks (mono) |

### Typography Rules

1. **Headings**: Always `Inter` with negative letter-spacing for tightness.
2. **Body**: `Inter 400` at 16px base. Never go below 14px for readable content.
3. **Code & Data**: Always `JetBrains Mono`. Used for AI responses in code blocks, console output, metrics.
4. **Overlines**: Always uppercase with wide letter-spacing. Used for section labels.
5. **Numbers in dashboards**: Use `JetBrains Mono` for tabular alignment.
6. **Maximum line width**: 72ch for body text, 48ch for narrow columns.

---

## 4. Spacing

### Scale (based on 4px grid)

| Token | Value | Usage |
|-------|-------|-------|
| `--space-1` | 4px | Inline element gaps, icon padding |
| `--space-2` | 8px | Tight component gaps, small padding |
| `--space-3` | 12px | Default inline padding |
| `--space-4` | 16px | Default component padding |
| `--space-5` | 20px | Medium gaps |
| `--space-6` | 24px | Card padding, section gaps |
| `--space-8` | 32px | Large section padding |
| `--space-10` | 40px | Panel padding |
| `--space-12` | 48px | Section separators |
| `--space-16` | 64px | Page-level padding |
| `--space-20` | 80px | Major section breaks |
| `--space-24` | 96px | Hero sections, viewport margins |

### Rules

1. **All spacing must use tokens.** No magic numbers like `13px` or `27px`.
2. **Consistent internal padding**: Cards use `--space-6`, modals use `--space-8`.
3. **Component gaps**: Use `gap` property, not margins between siblings.
4. **Page gutters**: `--space-4` on mobile, `--space-8` on tablet, `--space-16` on desktop.

---

## 5. Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-xs` | 4px | Small chips, tags |
| `--radius-sm` | 6px | Inputs, small buttons |
| `--radius-md` | 8px | Buttons, tooltips |
| `--radius-lg` | 12px | Cards, panels |
| `--radius-xl` | 16px | Modals, large cards |
| `--radius-2xl` | 24px | Feature cards, hero elements |
| `--radius-full` | 9999px | Avatars, pills, circular buttons |

---

## 6. Shadows & Elevation

### Elevation Levels

| Level | Shadow | Usage |
|-------|--------|-------|
| `--elevation-0` | `none` | Flat elements |
| `--elevation-1` | `0 1px 2px hsla(0,0%,0%,0.3), 0 1px 3px hsla(0,0%,0%,0.15)` | Cards, dropdowns |
| `--elevation-2` | `0 4px 8px hsla(0,0%,0%,0.35), 0 2px 4px hsla(0,0%,0%,0.2)` | Floating panels |
| `--elevation-3` | `0 8px 24px hsla(0,0%,0%,0.4), 0 4px 8px hsla(0,0%,0%,0.25)` | Modals, overlays |
| `--elevation-4` | `0 16px 48px hsla(0,0%,0%,0.5), 0 8px 16px hsla(0,0%,0%,0.3)` | Full-screen overlays |

### Glow Shadows (for interactive/active elements)

```css
--glow-primary:   0 0 20px hsla(210, 100%, 60%, 0.15), 0 0 40px hsla(210, 100%, 60%, 0.05);
--glow-secondary: 0 0 20px hsla(275, 80%, 65%, 0.15), 0 0 40px hsla(275, 80%, 65%, 0.05);
--glow-cyan:      0 0 20px hsla(185, 100%, 55%, 0.15), 0 0 40px hsla(185, 100%, 55%, 0.05);
--glow-intense:   0 0 30px hsla(210, 100%, 60%, 0.3), 0 0 60px hsla(210, 100%, 60%, 0.1);
```

---

## 7. Glassmorphism

### Glass Levels

| Level | Properties | Usage |
|-------|-----------|-------|
| **Glass Subtle** | `background: hsla(225, 20%, 10%, 0.4); backdrop-filter: blur(12px); border: 1px solid hsla(0,0%,100%,0.04);` | Background panels, sidebar |
| **Glass Standard** | `background: hsla(225, 20%, 12%, 0.6); backdrop-filter: blur(20px); border: 1px solid hsla(0,0%,100%,0.08);` | Cards, chat bubbles |
| **Glass Prominent** | `background: hsla(225, 20%, 14%, 0.7); backdrop-filter: blur(32px); border: 1px solid hsla(0,0%,100%,0.12);` | Modals, dropdowns |
| **Glass Active** | `background: hsla(210, 60%, 20%, 0.5); backdrop-filter: blur(20px); border: 1px solid hsla(210,100%,60%,0.2);` | Active/selected items |

### Noise Texture

Add a subtle noise overlay to glass elements for depth:

```css
.glass::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: url('/textures/noise.png');
  opacity: 0.03;
  mix-blend-mode: overlay;
  pointer-events: none;
  border-radius: inherit;
}
```

### Glass Rules

1. **Never stack more than 2 glass layers** — performance degrades with nested `backdrop-filter`.
2. **Always include a border** — without it, glass panels lose definition against dark backgrounds.
3. **Avoid glass on scrollable content** — `backdrop-filter` causes scroll jank on lower-end devices.
4. **Fallback**: If `backdrop-filter` is unsupported, use solid `--color-bg-elevated` as fallback.

---

## 8. Animations & Motion Principles

### Core Easing Curves

```css
/* Apple-style spring — default for most animations */
--ease-spring:      cubic-bezier(0.16, 1, 0.3, 1);

/* Smooth deceleration — for elements entering the viewport */
--ease-out:         cubic-bezier(0, 0, 0.2, 1);

/* Smooth acceleration — for elements leaving */
--ease-in:          cubic-bezier(0.4, 0, 1, 1);

/* Standard ease — for color/opacity transitions */
--ease-standard:    cubic-bezier(0.4, 0, 0.2, 1);

/* Bounce — sparingly, for celebratory moments */
--ease-bounce:      cubic-bezier(0.34, 1.56, 0.64, 1);
```

### Duration Scale

| Token | Value | Usage |
|-------|-------|-------|
| `--duration-instant` | 100ms | Opacity, color changes |
| `--duration-fast` | 150ms | Button hover, focus rings |
| `--duration-normal` | 250ms | Panel transitions, dropdowns |
| `--duration-slow` | 400ms | Page transitions, modals |
| `--duration-dramatic` | 600ms | Hero animations, 3D transitions |
| `--duration-cinematic` | 1000ms | Intro sequences, complex choreography |

### Motion Principles

| Principle | Rule |
|-----------|------|
| **Purposeful** | Every animation must communicate state change. No animation for decoration alone. |
| **Hierarchical** | Primary actions animate first, secondary follow. Creates visual rhythm. |
| **Interruptible** | All animations must be interruptible. Never lock the user out during a transition. |
| **Reduced Motion** | Respect `prefers-reduced-motion`. Disable transforms, keep opacity fades. |
| **Performance** | Only animate `transform` and `opacity`. Never animate `width`, `height`, `top`, `left`. |
| **Consistent** | Same type of action → same animation. Enter = fade up. Exit = fade down. |

### Animation Library

| Animation | Properties | Easing | Duration | Use Case |
|-----------|-----------|--------|----------|----------|
| **Fade In** | opacity: 0→1 | ease-out | 250ms | Elements appearing |
| **Fade Up** | opacity: 0→1, translateY: 16px→0 | spring | 400ms | Cards, list items entering |
| **Fade Down** | opacity: 1→0, translateY: 0→8px | ease-in | 200ms | Elements leaving |
| **Scale In** | opacity: 0→1, scale: 0.95→1 | spring | 300ms | Modals, tooltips |
| **Scale Out** | opacity: 1→0, scale: 1→0.95 | ease-in | 200ms | Closing modals |
| **Slide Right** | translateX: -100%→0 | spring | 400ms | Sidebar opening |
| **Slide Left** | translateX: 0→-100% | ease-in | 300ms | Sidebar closing |
| **Glow Pulse** | box-shadow pulse | standard | 2000ms (infinite) | Active/processing state |
| **Typing Cursor** | opacity blink | step-end | 1000ms (infinite) | AI response streaming |
| **Shimmer** | background-position sweep | linear | 1500ms (infinite) | Loading skeletons |

### Stagger Pattern

When animating lists (chat history, notifications), stagger children:

```css
/* Each child delayed by 50ms × index, max 10 items staggered */
--stagger-delay: 50ms;
--stagger-max: 10;
```

### GSAP Usage Guidelines

- Use GSAP **only** for complex, multi-step choreography (intro sequence, 3D transitions).
- Use Framer Motion for **component-level** animations (mount/unmount, layout, drag).
- **Never** use both GSAP and Framer Motion on the same element.
- GSAP timelines should be created in `useEffect` and cleaned up on unmount.

---

## 9. 3D Guidelines

### React Three Fiber Standards

| Property | Value | Reason |
|----------|-------|--------|
| **Canvas size** | Full viewport background, `z-index: -1` | Non-blocking, decorative layer |
| **Max polygons** | 50,000 for background effects | Performance budget |
| **Frame rate target** | 60fps on mid-range devices | Smooth without draining battery |
| **Anti-aliasing** | Enabled, `samples: 4` | Visual quality |
| **Tone mapping** | `ACESFilmicToneMapping` | Cinematic color grading |
| **Pixel ratio** | `Math.min(window.devicePixelRatio, 2)` | Prevent 3x rendering on high-DPI |

### Particle System Rules

1. **Particle count**: 500–2000 particles max. Scale down on mobile.
2. **Colors**: Use accent palette only (`accent-primary`, `accent-cyan`, `accent-secondary`).
3. **Movement**: Slow, organic drift. Speed ≤ 0.5 units/second.
4. **Interaction**: Subtle parallax on mouse move (3-5px offset per 100px movement).
5. **Opacity**: Base 0.2–0.6. Never fully opaque — particles are atmosphere, not content.
6. **Size**: 1–3px. Vary with depth for perspective.

### Performance Rules

1. **Use `drei` helpers**: `<Stars>`, `<Float>`, `<PointMaterial>` — don't reinvent.
2. **Frustum culling**: Enable on all meshes.
3. **Disposal**: Clean up geometries/materials on unmount via `useEffect` cleanup.
4. **Mobile**: Reduce particle count by 60%, disable post-processing.
5. **Reduced Motion**: Replace animation with static render. Particles visible but stationary.

### 3D Integration Zones

| Zone | Effect | Priority |
|------|--------|----------|
| Landing page | Full particle field + logo animation | Required |
| Auth pages | Subtle particle background, reduced density | Required |
| Neural Workspace | Minimal ambient particles, very subtle | Optional |
| AI Console | None — focus on content | None |

---

## 10. Iconography

### Icon System

| Property | Standard |
|----------|----------|
| **Library** | [Lucide React](https://lucide.dev) |
| **Style** | Outline (1.5px stroke) — matches Inter's geometric feel |
| **Size Scale** | 16px (inline), 20px (default), 24px (large), 32px (feature icons) |
| **Color** | Inherits `currentColor` — never hardcoded |

### Icon Usage Rules

1. **Sidebar**: 20px icons, `--color-text-secondary` default, `--color-accent-primary` when active.
2. **Buttons**: 16px inline icons, placed left of text with 8px gap.
3. **Empty states**: 48px icons, `--color-text-tertiary`, centered.
4. **Status indicators**: Use colored dots (8px) next to icons, not colored icons.

### Custom Icons

If Lucide doesn't have what we need:
- Design on 24×24 grid
- 1.5px stroke weight
- Round line caps and joins
- Export as SVG, import as React component

---

## 11. Component Naming Convention

### File Naming

```
PascalCase.tsx          # Components: GlassPanel.tsx, MessageBubble.tsx
camelCase.ts            # Utilities, hooks: useAuth.ts, formatDate.ts
camelCase.css            # Styles: animations.css
SCREAMING_SNAKE.ts      # Constants: API_ENDPOINTS.ts (only in constants files)
kebab-case/             # Directories: event-center/, system-core/
```

### Component Naming

| Pattern | Example | Rule |
|---------|---------|------|
| **UI Primitives** | `Button`, `Input`, `Modal` | Generic, no feature context |
| **Layout** | `Sidebar`, `Topbar`, `OSShell` | Structural positioning |
| **Feature** | `ConsoleInput`, `MessageBubble` | Prefixed with feature area |
| **Motion** | `FadeIn`, `SlideIn`, `GlowPulse` | Action-based names |
| **Three.js** | `ParticleField`, `NeuralBackground` | Descriptive of visual |

### Props Naming

```typescript
// Boolean props: is/has/should prefix
interface ButtonProps {
  isLoading: boolean;
  isDisabled: boolean;
  hasIcon: boolean;
}

// Event handlers: on prefix
interface InputProps {
  onChange: (value: string) => void;
  onFocus: () => void;
  onBlur: () => void;
}

// Variants: union types, not booleans
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'ghost' | 'danger';
  size: 'sm' | 'md' | 'lg';
}
```

### Hook Naming

```typescript
useAuth()           // Feature-level: manages auth state
useConsole()        // Feature-level: manages AI Console state
useMediaQuery()     // Utility: generic reusable hook
useDebounce()       // Utility: generic reusable hook
```

### Store Naming (Zustand)

```typescript
// File: authStore.ts
// Export: useAuthStore
// Shape: { state, actions }

export const useAuthStore = create<AuthState & AuthActions>()(...)
```

---

## 12. Responsive Breakpoints

### Breakpoint Scale

| Token | Value | Target |
|-------|-------|--------|
| `--bp-mobile` | 0–639px | Mobile phones (portrait) |
| `--bp-tablet` | 640–1023px | Tablets, large phones (landscape) |
| `--bp-desktop` | 1024–1439px | Laptops, small monitors |
| `--bp-wide` | 1440–1919px | Standard monitors |
| `--bp-ultrawide` | 1920px+ | Large monitors, ultrawide |

### TailwindCSS v4 Breakpoints

```css
/* In globals.css or tailwind config */
@theme {
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1440px;
  --breakpoint-2xl: 1920px;
}
```

### Responsive Rules

| Element | Mobile | Tablet | Desktop |
|---------|--------|--------|---------|
| **Sidebar** | Hidden (hamburger menu) | Collapsed (icons only, 64px) | Expanded (240px) |
| **Topbar** | Simplified (logo + menu) | Full (breadcrumb + search + actions) | Full |
| **AI Console** | Full width | Full width | Full width with sidebar visible |
| **Cards** | Single column | 2 columns | 3–4 columns |
| **Typography** | H1: 32px, Body: 16px | H1: 40px, Body: 16px | H1: 48px, Body: 16px |
| **3D Background** | Reduced particles (30%) | Standard particles (60%) | Full particles (100%) |
| **Padding** | `--space-4` | `--space-8` | `--space-16` |

### Touch Targets

- **Minimum**: 44×44px for all interactive elements on mobile.
- **Recommended**: 48×48px for primary actions.
- **Spacing between targets**: Minimum 8px gap.

---

## 13. Accessibility

### Standards

- **Target**: WCAG 2.2 Level AA compliance.
- **Testing**: Every component must pass automated a11y checks.

### Color Contrast

| Context | Minimum Ratio |
|---------|--------------|
| Body text on background | 4.5:1 |
| Large text (≥24px) on background | 3:1 |
| UI component borders | 3:1 |
| Focus indicators | 3:1 |

> `--color-text-primary` (95% white) on `--color-bg-primary` (6% gray) = **13.8:1** ✓
> `--color-text-secondary` (55% gray) on `--color-bg-primary` = **5.2:1** ✓
> `--color-accent-primary` on `--color-bg-primary` = **5.8:1** ✓

### Focus Management

```css
/* Default focus ring for all interactive elements */
:focus-visible {
  outline: 2px solid var(--color-border-focus);
  outline-offset: 2px;
  border-radius: var(--radius-sm);
}

/* Never use outline: none without providing alternative focus indicator */
```

### Keyboard Navigation

1. **Tab order**: Logical, top-to-bottom, left-to-right.
2. **Skip links**: "Skip to main content" link on every page.
3. **Escape**: Closes modals, dropdowns, sidebars.
4. **Arrow keys**: Navigate within component groups (sidebar items, chat list).
5. **Enter/Space**: Activate buttons and toggles.

### ARIA Rules

| Pattern | ARIA |
|---------|------|
| Glass panels | `role="region"` with `aria-label` |
| Sidebar | `role="navigation"` with `aria-label="Main navigation"` |
| Chat messages | `role="log"` with `aria-live="polite"` |
| Streaming text | `aria-live="polite"` on the container |
| Notifications | `role="alert"` for urgent, `role="status"` for informational |
| Loading states | `aria-busy="true"` on the loading container |
| Modal | `role="dialog"`, `aria-modal="true"`, focus trap |

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
  
  /* Keep opacity transitions for feedback */
  .motion-safe-opacity {
    transition-duration: 150ms !important;
    transition-property: opacity !important;
  }
}
```

### Screen Reader Considerations

1. **AI responses**: Announce when response starts and completes, not every token.
2. **Voice button**: Clear labels: "Start voice recording" / "Stop recording".
3. **3D background**: `aria-hidden="true"` — purely decorative.
4. **Icon-only buttons**: Always include `aria-label`.

---

## 14. Dark Theme Specification

### Phase 1: Dark Only

YUGI-AI launches with a single dark theme. This is the only theme in Phase 1.
The color palette above IS the dark theme.

### Phase 2 Preparation

The architecture should support theme switching via CSS custom properties:

```css
/* All colors defined as custom properties in :root */
:root {
  color-scheme: dark;
  /* All --color-* tokens defined here */
}

/* Future: light theme override */
[data-theme="light"] {
  --color-bg-primary: hsl(225, 20%, 97%);
  --color-text-primary: hsl(225, 25%, 10%);
  /* ...override all tokens... */
}
```

### Theme Rules

1. **Use CSS custom properties** for all colors. Never use raw HSL in components.
2. **Test new components** against the dark palette before shipping.
3. **Glass effects**: Adjust opacity values per theme (darker glass on light backgrounds).

---

## 15. Sound Design

### Phase 1: Silent

No sounds in Phase 1. Architecture should support optional UI sounds.

### Future Sound Tokens

| Event | Sound | Duration |
|-------|-------|----------|
| Message sent | Soft "whoosh" | 200ms |
| Message received | Subtle chime | 300ms |
| Notification | Distinct tone | 400ms |
| Error | Low tone | 300ms |
| Voice recording start | Click | 100ms |
| Voice recording stop | Click | 100ms |

### Sound Rules (Future)

1. **Always respect user preference**: Sounds disabled by default.
2. **Volume**: Maximum 40% system volume.
3. **Format**: WebM Opus for compression, MP3 fallback.
4. **Preload**: Load sounds during idle time via `requestIdleCallback`.

---

## Appendix: CSS Variable Template

This is the complete set of CSS custom properties to include in `globals.css`:

```css
@theme {
  /* ===== COLORS ===== */
  --color-bg-void: hsl(225, 30%, 3%);
  --color-bg-primary: hsl(225, 25%, 6%);
  --color-bg-secondary: hsl(225, 20%, 10%);
  --color-bg-elevated: hsl(225, 18%, 14%);
  --color-bg-hover: hsl(225, 16%, 18%);

  --color-accent-primary: hsl(210, 100%, 60%);
  --color-accent-primary-dim: hsl(210, 80%, 45%);
  --color-accent-primary-bright: hsl(210, 100%, 72%);
  --color-accent-secondary: hsl(275, 80%, 65%);
  --color-accent-secondary-dim: hsl(275, 60%, 50%);
  --color-accent-cyan: hsl(185, 100%, 55%);
  --color-accent-cyan-dim: hsl(185, 80%, 40%);

  --color-success: hsl(145, 70%, 50%);
  --color-warning: hsl(35, 95%, 55%);
  --color-error: hsl(0, 75%, 55%);
  --color-info: hsl(210, 100%, 60%);

  --color-text-primary: hsl(0, 0%, 95%);
  --color-text-secondary: hsl(225, 15%, 55%);
  --color-text-tertiary: hsl(225, 12%, 38%);
  --color-text-accent: hsl(210, 100%, 68%);

  --color-border-default: hsla(0, 0%, 100%, 0.06);
  --color-border-hover: hsla(0, 0%, 100%, 0.12);
  --color-border-focus: hsl(210, 100%, 60%);

  /* ===== TYPOGRAPHY ===== */
  --font-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  /* ===== SPACING ===== */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;
  --space-20: 80px;
  --space-24: 96px;

  /* ===== RADIUS ===== */
  --radius-xs: 4px;
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-2xl: 24px;
  --radius-full: 9999px;

  /* ===== ANIMATION ===== */
  --ease-spring: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-standard: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);

  --duration-instant: 100ms;
  --duration-fast: 150ms;
  --duration-normal: 250ms;
  --duration-slow: 400ms;
  --duration-dramatic: 600ms;
  --duration-cinematic: 1000ms;

  /* ===== BREAKPOINTS ===== */
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1440px;
  --breakpoint-2xl: 1920px;
}
```

---

> **This document is the single source of truth for all visual decisions.**
> Every component, every page, every module must reference these tokens.
> If a value doesn't exist here, propose it as an addition before using it.
