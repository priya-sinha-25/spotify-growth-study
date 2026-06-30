---
name: Sonic Dark
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#393939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1b1b1b'
  surface-container: '#1f1f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353535'
  on-surface: '#e2e2e2'
  on-surface-variant: '#bccbb9'
  inverse-surface: '#e2e2e2'
  inverse-on-surface: '#303030'
  outline: '#869585'
  outline-variant: '#3d4a3d'
  surface-tint: '#53e076'
  primary: '#53e076'
  on-primary: '#003914'
  primary-container: '#1db954'
  on-primary-container: '#004118'
  inverse-primary: '#006e2d'
  secondary: '#c8c6c5'
  on-secondary: '#313030'
  secondary-container: '#4a4949'
  on-secondary-container: '#bab8b7'
  tertiary: '#c8c6c5'
  on-tertiary: '#313030'
  tertiary-container: '#a3a1a0'
  on-tertiary-container: '#383838'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#72fe8f'
  primary-fixed-dim: '#53e076'
  on-primary-fixed: '#002108'
  on-primary-fixed-variant: '#005320'
  secondary-fixed: '#e5e2e1'
  secondary-fixed-dim: '#c8c6c5'
  on-secondary-fixed: '#1c1b1b'
  on-secondary-fixed-variant: '#474646'
  tertiary-fixed: '#e5e2e1'
  tertiary-fixed-dim: '#c8c6c5'
  on-tertiary-fixed: '#1c1b1b'
  on-tertiary-fixed-variant: '#474746'
  background: '#131313'
  on-background: '#e2e2e2'
  surface-variant: '#353535'
typography:
  display-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 48px
    fontWeight: '800'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '800'
    lineHeight: 40px
    letterSpacing: -0.02em
  display-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '700'
    lineHeight: 28px
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '500'
    lineHeight: 24px
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 14px
  display-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '800'
    lineHeight: 40px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  sidebar-width: 350px
  player-height: 90px
  navbar-height: 64px
  gutter: 24px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 32px
---

## Brand & Style
The design system is engineered to evoke a cinematic, high-fidelity atmosphere tailored for music and podcast discovery. The aesthetic is "Dark Modernism"—leveraging deep blacks and subtle grays to make vibrant album art and media content the focal point. 

The target audience is tech-savvy music lovers who value a sleek, professional interface that recedes into the background during use. By utilizing high-contrast accents against a monochromatic base, the UI feels both premium and energetic. The emotional response is one of immersion and focus, ensuring the platform feels like a dedicated "listening room" rather than a utility app.

## Colors
The color palette is strictly dark to enhance the visual pop of metadata and album covers. 

- **Primary Green (#1DB954):** Reserved exclusively for high-priority actions, active states, and playback controls. It serves as the primary "energy" source of the UI.
- **Pure Black (#000000):** Used for the structural foundations—the persistent sidebar and the bottom player bar—to create a sense of groundedness and depth.
- **Deep Gray (#121212):** The surface color for the main scrollable content area, providing a slightly softer backdrop than pure black for long-term legibility.
- **Surface Gray (#181818):** Used for interactive containers like cards, list items, and hover states to provide subtle elevation without needing shadows.
- **Typography:** Primary text is pure white for maximum legibility, while secondary text and metadata use a muted gray (#B3B3B3) to maintain visual hierarchy.

## Typography
The system uses **Plus Jakarta Sans** to replicate a clean, geometric, and bold "Circular" aesthetic. 

- **Weight & Emphasis:** Headlines use Bold or ExtraBold weights to command attention. Body text is kept at Medium (500) to ensure clarity against dark backgrounds.
- **Scale:** Large display sizes are used for playlist titles and artist names. Scale down significantly for secondary metadata (e.g., track durations, listener counts) using the `label` roles.
- **Letter Spacing:** Headlines use slightly negative letter-spacing to feel tighter and more "editorial," while small labels use positive tracking for legibility at small sizes.

## Layout & Spacing
The layout is a structured, three-pane architecture designed for multi-tasking and quick navigation.

- **Sidebar (Fixed):** A 350px width panel on the left for navigation and library management. It uses a `#000000` background.
- **Main Panel (Fluid):** The central content area that adapts to the window size. It contains a top navigation bar (64px) and utilizes horizontal scrolling "shelves" for content discovery.
- **Player Bar (Fixed):** A 90px height persistent bar at the bottom for playback controls and "Now Playing" info.
- **Rhythm:** An 8px base grid is used for all internal spacing. Content within the main panel should maintain a 24px outer margin (gutter) for breathability.

## Elevation & Depth
In this design system, depth is achieved through **Tonal Layering** rather than traditional shadows. 

1. **Level 0 (#000000):** The base structural layer (Sidebar, Player Bar).
2. **Level 1 (#121212):** The primary workspace/content area.
3. **Level 2 (#181818):** Interactive cards, hover states, and context menus.
4. **Level 3 (#282828):** Active focus states or tooltips.

When album art is present, a subtle "ambient glow" or gradient can be applied to the top of the main panel, pulling the dominant color from the image and fading it into the `#121212` background.

## Shapes
The shape language combines geometric rigor with soft, approachable edges.

- **Standard Containers:** Cards and input fields use a `rounded-lg` (8px-12px) corner radius to feel modern and polished.
- **Media:** Album art and artist profile images should always maintain a consistent 8px radius, except for artist profile icons which may be circular.
- **Interactive Elements:** Buttons utilize a full "pill" shape (rounded-xl) to distinguish them as high-intent interactive zones.

## Components

### Buttons
- **Primary:** Pill-shaped, Spotify Green background, black text. Bold weight.
- **Secondary:** Pill-shaped, white or transparent with a white border.
- **Icon Buttons:** No background; icon color changes from `#B3B3B3` to `#FFFFFF` on hover.

### Cards
- **Media Card:** `#181818` background, 8px-12px padding. Features a hidden "Play" button that appears in the bottom right of the image on hover using a green circle and black icon.

### Lists & Tables
- **Track List:** Uses a flat row structure. On hover, the background changes to `#FFFFFF1A` (10% opacity white) and the track number icon switches to a play icon.
- **Typography:** Track title in `body-md` (white), Artist/Album in `label-sm` (`#B3B3B3`).

### Input Fields
- **Search Bar:** Rounded-xl (pill-shaped), `#242424` background, white text. Left-aligned search icon.

### Interaction States
- **Hover:** All surface layers (`#181818`) should brighten slightly or increase in opacity when hovered to provide tactile feedback.
- **Active:** Elements being clicked or "Active" navigation links should use the Primary Green as an indicator (e.g., a small dot or a 2px vertical bar).