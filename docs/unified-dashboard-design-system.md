# ComfyUI Unified Dashboard - Design System

## Overview

The ComfyUI Unified Dashboard consolidates 5 fragmented UIs (ComfyUI, Preset Manager, Studio, Code Server, Jupyter) into a single, cohesive interface using htmx + Alpine.js + Tailwind CSS.

## Design Philosophy

**"Foxy" Design Principles:**
- **Bold**: Strong accent colors, confident typography
- **Dynamic**: Smooth animations, micro-interactions
- **Modern**: Contemporary layout, glassmorphism touches
- **Focused**: Clear hierarchy, purposeful elements
- **Delightful**: Subtle animations, satisfying interactions

## Color Palette

### Dark Theme (Default)

```css
/* Core Colors */
--bg-primary: #0a0a0f      /* Deepest background */
--bg-secondary: #12121a    /* Card/sidebar background */
--bg-tertiary: #1a1a24     /* Input/background element */
--bg-elevated: #222230     /* Modal/dropdown */
--bg-hover: #2a2a3a        /* Hover state */
--bg-active: #323248       /* Active/selected */

/* Accent Colors */
--accent-primary: #f97316  /* Orange - main CTA */
--accent-secondary: #8b5cf6 /* Purple - secondary actions */
--accent-success: #22c55e  /* Green - success states */
--accent-warning: #f59e0b  /* Amber - warnings */
--accent-error: #ef4444    /* Red - errors */
--accent-info: #3b82f6     /* Blue - informational */

/* Text Colors */
--text-primary: #f1f5f9    /* Main text */
--text-secondary: #94a3b8  /* Secondary text */
--text-tertiary: #64748b   /* Tertiary/disabled */
--text-inverse: #0a0a0f    /* Text on accent */

/* Border Colors */
--border-subtle: rgba(255, 255, 255, 0.06)
--border-medium: rgba(255, 255, 255, 0.10)
--border-strong: rgba(255, 255, 255, 0.15)
```

### Semantic Color Usage

| Purpose | Color | Usage |
|---------|-------|-------|
| Primary CTAs | Orange | Generate, Install, Save |
| Secondary Actions | Purple | Cancel, Back, Details |
| Success States | Green | Complete, Installed, Running |
| Warning States | Amber | Partial, Moderate, Caution |
| Error States | Red | Failed, Error, Critical |
| Informational | Blue | Info, Help, Documentation |

## Typography Scale

```css
/* Font Families */
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif
--font-mono: 'JetBrains Mono', 'SF Mono', Consolas, monospace

/* Type Scale */
heading-xl: 32px / 700 / -0.03em   /* Page headers */
heading-lg: 24px / 700 / -0.02em   /* Section headers */
heading-md: 20px / 600 / -0.02em   /* Subsection headers */
heading-sm: 16px / 600 / normal    /* Card titles */
body: 14px / 400 / normal          /* Body text */
caption: 12px / 400 / normal       /* Meta text */
label: 11px / 600 / normal         /* Labels, badges */
```

### Typography Hierarchy

1. **H1 (32px)**: Page titles - "Welcome back", "Generate", "Models"
2. **H2 (24px)**: Section headers - "System Resources", "Recent Activity"
3. **H3 (20px)**: Subsections - "Video Models", "Image Models"
4. **H4 (16px)**: Card titles - "WAN 2.1 14B", "Txt2Img Workflow"
5. **Body (14px)**: Main content, descriptions, labels
6. **Caption (12px)**: Meta information, timestamps, hints
7. **Label (11px)**: Badges, tags, small indicators

## Spacing System

```css
--space-xs: 4px    /* Tight spacing */
--space-sm: 8px    /* Compact spacing */
--space-md: 16px   /* Default spacing */
--space-lg: 24px   /* Relaxed spacing */
--space-xl: 32px   /* Section spacing */
--space-2xl: 48px  /* Large section spacing */
```

### Spacing Guidelines

- **4px**: Icon padding, tight gaps
- **8px**: Small components, badges, button padding
- **16px**: Default gap between elements, card padding
- **24px**: Section margins, large padding
- **32px**: Major section spacing
- **48px**: Page-level spacing

## Border Radius

```css
--radius-sm: 6px    /* Small elements, badges */
--radius-md: 10px   /* Buttons, inputs */
--radius-lg: 16px   /* Cards, panels */
--radius-xl: 24px   /* Large cards, modals */
--radius-full: 9999px /* Pills, avatars */
```

## Shadows

```css
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3)
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4)
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5)
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.6)
--shadow-glow: 0 0 20px rgba(249, 115, 22, 0.15)
```

## Transitions

```css
--transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1)
--transition-base: 200ms cubic-bezier(0.4, 0, 0.2, 1)
--transition-slow: 300ms cubic-bezier(0.4, 0, 0.2, 1)
```

## Section Wireframes

### 1. Home Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  ┌─────────┐  Welcome back                          [↻] [+] │
│  │   C     │  Your AI workspace is ready                     │
│  └─────────┘                                                 │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                 │   │
│  │ │ 1,284│ │  12  │ │24.5GB│ │  8   │                 │   │
│  │ │Gener.│ │Models│ │Storage│ │Workfl.│                 │   │
│  │ └──────┘ └──────┘ └──────┘ └──────┘                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  Quick Actions                                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │    ▶     │ │    ↓     │ │    ⚡     │ │    ◉     │     │
│  │ Run      │ │ Install  │ │ Quick    │ │ Check    │     │
│  │ Workflow │ │ Model    │ │ Generate │ │ Status   │     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
│                                                              │
│  System Resources                    [View Details →]      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │ GPU Mem  │ │ RAM      │ │ Disk     │ │ GPU Temp │     │
│  │ 14.2/24G │ │ 42.8/64G │ │ 24.5/500G│ │   68°C   │     │
│  │ ████░░░░ │ │ █████░░░ │ │ ░░░░░░░░ │ │ █████░░░ │     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
│                                                              │
│  Recent Activity                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ✓ Image generation completed    [Complete]  2m ago  │   │
│  │ ◫ Model download in progress     [67%]     3m left  │   │
│  │ ✕ Generation failed              [Failed]   OOM     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Key Elements:**
- Stats cards with trends and icons
- Quick action buttons with hover effects
- Resource monitors with color-coded status
- Activity feed with status indicators

### 2. Generate Section

```
┌─────────────────────────────────────────────────────────────┐
│  ┌─────────┐  Generate                            [←] [→]  │
│  │   C     │  Simplified workflow execution                      │
│  └─────────┘                                                 │
│                                                              │
│  ┌─────────────────────┐ ┌─────────────────────────────┐   │
│  │   Workflow Type     │ │      Model Selection        │   │
│  │ ◉ Text to Image     │ │ ◉ WAN 2.1 14B              │   │
│  │ ○ Image to Image    │ │ ○ LTX Video                │   │
│  │ ○ Text to Video     │ │ ○ Hunyuan Video            │   │
│  │ ○ Image to Video    │ │ ○ Cosmos                   │   │
│  └─────────────────────┘ └─────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Prompt                                               │   │
│  │ ┌─────────────────────────────────────────────────┐ │   │
│  │ │ A serene mountain landscape at sunset, with...  │ │   │
│  │ └─────────────────────────────────────────────────┘ │   │
│  │ [Enhance] [Randomize] [Clear]                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────┐ ┌─────────────────────────────┐       │
│  │   Parameters    │ │      Advanced               │       │
│  │ Width:  1024    │ │ Steps:        20           │       │
│  │ Height: 1024    │ │ CFG Scale:    7.5          │       │
│  │ Seed:   [Random]│ │ Sampler:     DPM++ 2M Karras│       │
│  └─────────────────┘ │ Scheduler:   Karras        │       │
│                      │ Seed:        [Random]       │       │
│                      └─────────────────────────────┘       │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    [⚡ Generate]                     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Key Elements:**
- Workflow type selector (radio group)
- Model dropdown with search
- Large prompt input with enhancement tools
- Basic parameters in left column
- Advanced options in right column (collapsible)
- Prominent generate button

### 3. Models Section

```
┌─────────────────────────────────────────────────────────────┐
│  ┌─────────┐  Models                              [Search]  │
│  │   C     │  12 installed • 44 available                    │
│  └─────────┘                                                 │
│                                                              │
│  [All] [Video] [Image] [Audio] [Installed] [Updates]        │
│                                                              │
│  ┌────────────────────┐ ┌────────────────────┐             │
│  │ [INSTALLED]        │ │ [AVAILABLE]        │             │
│  │ WAN 2.1 14B       │ │ LTX Video          │             │
│  │ State-of-the-art  │ │ Lightning-fast     │             │
│  │ text-to-video...  │ │ text-to-video...   │             │
│  │ ◉ 14.5GB ◈ Video │ │ ◉ 2.1GB ◈ Video   │             │
│  │ [Details] [Gen]   │ │ [Details] [Install]│             │
│  └────────────────────┘ └────────────────────┘             │
│                                                              │
│  ┌────────────────────┐ ┌────────────────────┐             │
│  │ [DOWNLOADING]      │ │ [PARTIAL]          │             │
│  │ Hunyuan Video     │ │ FLUX.1-dev        │             │
│  │ ████████░░ 80%    │ │ ██████░░░░ 60%    │             │
│  │ 2.1GB / 8.2GB    │ │ 9.6GB / 16GB      │             │
│  │ ETA: 1m 24s       │ │ [Resume] [Cancel] │             │
│  │ [Pause] [Cancel]  │ └────────────────────┘             │
│  └────────────────────┘                                      │
│                                                              │
│  Storage: 24.5 GB / 500 GB                    [Manage →]    │
│  ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░           │
└─────────────────────────────────────────────────────────────┘
```

**Key Elements:**
- Category tabs with counts
- Model cards with badges (installed, available, downloading)
- Progress bars for active downloads
- Storage overview bar
- Search and filter functionality
- Batch operations support

### 4. Workflows Section

```
┌─────────────────────────────────────────────────────────────┐
│  ┌─────────┐  Workflows                           [+ New]   │
│  │   C     │  8 workflows • 156 runs total                       │
│  └─────────┘                                                 │
│                                                              │
│  [All] [Templates] [Custom] [Favorites] [Recent]            │
│                                                              │
│  ┌────────────────────┐ ┌────────────────────┐             │
│  │ ⭐ Txt2Img SDXL    │ │ Img2Img FLUX      │             │
│  │ Text-to-image with │ │ Transform images  │             │
│  │ SDXL model         │ │ using FLUX        │             │
│  │ ◈ 156 runs        │ │ ◈ 42 runs         │             │
│  │ [▶ Run] [⚙ Edit]  │ │ [▶ Run] [⚙ Edit] │             │
│  └────────────────────┘ └────────────────────┘             │
│                                                              │
│  ┌────────────────────┐ ┌────────────────────┐             │
│  │ Video WAN          │ │ Upscale HQ         │             │
│  │ Generate videos    │ │ High-quality       │             │
│  │ from text prompts  │ │ upscaling          │             │
│  │ ◈ 28 runs         │ │ ◈ 86 runs         │             │
│  │ [▶ Run] [⚙ Edit]  │ │ [▶ Run] [⚙ Edit] │             │
│  └────────────────────┘ └────────────────────┘             │
│                                                              │
│  Recent Runs                                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ✓ Txt2Img SDXL    2m ago    [View] [Download]      │   │
│  │ ✓ Img2Img FLUX    5m ago    [View] [Download]      │   │
│  │ ✕ Video WAN       8m ago    [View] [Retry]         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Key Elements:**
- Template/Custom workflow tabs
- Workflow cards with run counts
- Quick actions (Run, Edit, Duplicate)
- Recent runs with direct links to outputs
- Favorite functionality
- Import/Export workflows

### 5. Settings Section

```
┌─────────────────────────────────────────────────────────────┐
│  ┌─────────┐  Settings                                            │
│  │   C     │  Configure your workspace                           │
│  └─────────┘                                                 │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ◉ General  ○ Models  ○ Performance  ○ Advanced     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  Appearance                                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Theme:       ◉ Dark  ○ Light  ○ System             │   │
│  │ Accent Color:◉ Orange ○ Purple ○ Blue ○ Green      │   │
│  │ Font Size:   ○ Small ◉ Medium ○ Large              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  Notifications                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ [✓] Show desktop notifications                      │   │
│  │ [✓] Play sound on completion                       │   │
│  │ [ ] Enable browser notifications                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  API Keys                                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Hugging Face:  [•••••••••••••]        [Update]      │   │
│  │ Civitai:       [Not configured]      [Add]         │   │
│  │ OpenAI:        [sk-•••••••••••]       [Update]      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    [Save Changes]                   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Key Elements:**
- Tabbed interface for setting categories
- Appearance settings (theme, accent, font)
- Notification preferences
- API key management with secure display
- Save/Cancel actions
- Reset to defaults option

### 6. Pro Mode (Link to ComfyUI)

```
┌─────────────────────────────────────────────────────────────┐
│  ┌─────────┐  Pro Mode                                            │
│  │   C     │  Advanced node-based editing                       │
│  └─────────┘                                                 │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                       │   │
│  │       ⬡                                            │   │
│  │    ComfyUI Pro                                      │   │
│  │                                                       │   │
│  │  Access the full node-based ComfyUI interface        │   │
│  │  for advanced workflow creation and automation.      │   │
│  │                                                       │   │
│  │  Features:                                            │   │
│  │  • Visual node editor                                │   │
│  │  • Custom node support                               │   │
│  │  • Workflow JSON import/export                       │   │
│  │  • API access                                        │   │
│  │                                                       │   │
│  │              [Launch ComfyUI Pro →]                  │   │
│  │                                                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  Quick Tips                                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ • Press Ctrl+S to save workflows                     │   │
│  │ • Drag nodes to connect them                         │   │
│  │ • Right-click for context menu                      │   │
│  │ • Double-click to add nodes                          │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Key Elements:**
- Clear call-to-action button
- Feature list
- Quick tips for new users
- Opens ComfyUI in new tab/window
- Seamless transition experience

## Component Breakdown

### Reusable UI Components

1. **Sidebar Navigation**
   - Brand logo/icon
   - Navigation items with icons
   - Active state indicator
   - Badge counts

2. **Stat Card**
   - Icon container
   - Value display
   - Label text
   - Trend indicator
   - Hover animation

3. **Preset/Model Card**
   - Status badge
   - Title
   - Description
   - Metadata (size, type)
   - Action buttons
   - Progress bar (for downloads)

4. **Resource Monitor**
   - Label
   - Current/total values
   - Progress bar
   - Status indicator
   - Color-coded states

5. **Activity Feed Item**
   - Icon
   - Title
   - Metadata
   - Status badge
   - Timestamp

6. **Button Variants**
   - Primary (orange)
   - Secondary (gray)
   - Ghost (transparent)
   - Sizes (sm, md, lg)

7. **Badge/Tag**
   - Status colors
   - Pill shape
   - Compact size

8. **Progress Bar**
   - Animated fill
   - Shimmer effect
   - Label display
   - Percentage text

9. **Input Field**
   - Label
   - Placeholder
   - Focus state
   - Validation states

10. **Toast Notification**
    - Icon
    - Title
    - Message
    - Close button
    - Auto-dismiss

## Real-time Update Patterns

### WebSocket Message Types

```javascript
// Progress updates
{
  type: 'progress',
  id: 'download-123',
  current: 6745000000,
  total: 8200000000,
  percentage: 67,
  speed: '45.2 MB/s',
  eta: 125
}

// Generation progress
{
  type: 'generation',
  id: 'gen-456',
  node: 'KSampler',
  step: 15,
  total: 20,
  preview: 'data:image/png;base64,...'
}

// Resource updates
{
  type: 'resources',
  gpu_memory: 14.2,
  system_memory: 42.8,
  disk_usage: 24.5,
  gpu_temp: 68
}

// Status changes
{
  type: 'status',
  entity: 'model-wan-14b',
  status: 'installed',
  message: 'WAN 2.1 14B installed successfully'
}
```

### Update Mechanisms

1. **htmx SSE (Server-Sent Events)**
   - For streaming progress updates
   - Real-time generation previews
   - Resource monitoring

2. **Alpine.js Reactive State**
   - Client-side UI updates
   - Modal/dropdown state
   - Form validation

3. **WebSocket**
   - Bidirectional communication
   - Real-time notifications
   - Multi-user collaboration

## Interaction Patterns

### Navigation
- Single sidebar with 6 sections
- Active state highlighted
- Badge counts for notifications
- Hover effects on all items

### Quick Actions
- Large, touch-friendly targets
- Icon + label layout
- Hover animations
- Context-aware actions

### Forms
- Clear labels above inputs
- Placeholder text for guidance
- Real-time validation
- Error messages inline
- Success feedback

### Modals/Dialogs
- Backdrop blur
- Smooth fade-in animation
- Close on backdrop click
- Escape key support
- Focus management

### Loading States
- Skeleton screens
- Progress bars with shimmer
- Spinner for indeterminate progress
- Text updates for context

### Feedback
- Toast notifications bottom-right
- Success: green checkmark
- Error: red X with message
- Warning: yellow alert
- Info: blue indicator

## Accessibility (WCAG 2.1 AA)

### Color Contrast
- All text meets 4.5:1 contrast ratio
- Interactive elements 3:1 contrast
- Focus indicators visible

### Keyboard Navigation
- Tab order logical
- Enter/Space for buttons
- Escape closes modals
- Arrow keys for lists

### Screen Reader Support
- Semantic HTML
- ARIA labels for icons
- Role attributes
- Live regions for updates

### Focus Management
- Visible focus indicators
- No focus traps
- Logical tab order
- Skip to content link

## Responsive Design

### Desktop (1024px+)
- Full sidebar (280px)
- Multi-column grids
- Hover effects enabled

### Tablet (768px - 1023px)
- Collapsible sidebar
- Two-column grids
- Touch-optimized targets

### Mobile (< 768px)
- Hidden sidebar (hamburger menu)
- Single-column layout
- Bottom navigation
- Full-width cards

## Technical Implementation

### htmx Patterns
```html
<!-- Load content dynamically -->
<div hx-get="/models" hx-trigger="load, every 5s">
  Loading models...
</div>

<!-- Update on progress -->
<div hx-ext="sse" sse-connect="/events/download" sse-swap="progress">
  <div id="progress-container"></div>
</div>

<!-- Form submission -->
<form hx-post="/generate" hx-swap="none">
  <input name="prompt" type="text">
  <button type="submit">Generate</button>
</form>
```

### Alpine.js Patterns
```javascript
// Component state
function modelCard() {
  return {
    expanded: false,
    installing: false,
    progress: 0,
    toggle() {
      this.expanded = !this.expanded
    },
    install() {
      this.installing = true
      // htmx request to install
    }
  }
}

// Global state
Alpine.store('notifications', {
  items: [],
  add(message, type) {
    this.items.push({ message, type, id: Date.now() })
  },
  remove(id) {
    this.items = this.items.filter(n => n.id !== id)
  }
})
```

### Tailwind CSS Configuration
```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        // Custom color palette
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      spacing: {
        // Custom spacing scale
      },
      borderRadius: {
        // Custom border radius values
      },
      boxShadow: {
        // Custom shadow values
        'glow': '0 0 20px rgba(249, 115, 22, 0.15)',
      },
      animation: {
        'shimmer': 'shimmer 2s infinite',
      },
      keyframes: {
        shimmer: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
      },
    },
  },
}
```

## Design Tokens

### Complete Token Reference

```css
/* Colors - Backgrounds */
--bg-primary: #0a0a0f;
--bg-secondary: #12121a;
--bg-tertiary: #1a1a24;
--bg-elevated: #222230;
--bg-hover: #2a2a3a;
--bg-active: #323248;

/* Colors - Accents */
--accent-primary: #f97316;
--accent-secondary: #8b5cf6;
--accent-success: #22c55e;
--accent-warning: #f59e0b;
--accent-error: #ef4444;
--accent-info: #3b82f6;

/* Colors - Text */
--text-primary: #f1f5f9;
--text-secondary: #94a3b8;
--text-tertiary: #64748b;
--text-inverse: #0a0a0f;

/* Colors - Border */
--border-subtle: rgba(255, 255, 255, 0.06);
--border-medium: rgba(255, 255, 255, 0.10);
--border-strong: rgba(255, 255, 255, 0.15);

/* Spacing */
--space-xs: 4px;
--space-sm: 8px;
--space-md: 16px;
--space-lg: 24px;
--space-xl: 32px;
--space-2xl: 48px;

/* Typography */
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
--font-mono: 'JetBrains Mono', 'SF Mono', Consolas, monospace;
--text-xs: 11px;
--text-sm: 12px;
--text-base: 14px;
--text-lg: 16px;
--text-xl: 20px;
--text-2xl: 24px;
--text-3xl: 32px;

/* Border Radius */
--radius-sm: 6px;
--radius-md: 10px;
--radius-lg: 16px;
--radius-xl: 24px;
--radius-full: 9999px;

/* Shadows */
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.6);
--shadow-glow: 0 0 20px rgba(249, 115, 22, 0.15);

/* Transitions */
--transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-base: 200ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-slow: 300ms cubic-bezier(0.4, 0, 0.2, 1);

/* Z-Index */
--z-base: 0;
--z-dropdown: 100;
--z-sticky: 200;
--z-modal: 500;
--z-toast: 600;
```

## Implementation Checklist

### Phase 1: Core Layout
- [ ] App shell with sidebar
- [ ] Navigation components
- [ ] Responsive breakpoints
- [ ] Base typography
- [ ] Color system integration

### Phase 2: Home Dashboard
- [ ] Stats cards
- [ ] Quick actions
- [ ] Resource monitors
- [ ] Activity feed
- [ ] Real-time updates via WebSocket

### Phase 3: Generate Section
- [ ] Workflow selector
- [ ] Model dropdown
- [ ] Prompt input
- [ ] Parameter controls
- [ ] Generation queue
- [ ] Results display

### Phase 4: Models Section
- [ ] Model cards
- [ ] Category tabs
- [ ] Search/filter
- [ ] Download manager
- [ ] Progress tracking
- [ ] Storage overview

### Phase 5: Workflows Section
- [ ] Workflow cards
- [ ] Template library
- [ ] Custom workflows
- [ ] Run history
- [ ] Import/export
- [ ] Favorite functionality

### Phase 6: Settings Section
- [ ] Tabbed interface
- [ ] Appearance settings
- [ ] Notifications
- [ ] API keys
- [ ] Preferences

### Phase 7: Pro Mode
- [ ] Launch button
- [ ] Feature list
- [ ] Quick tips
- [ ] Transition animation

### Phase 8: Polish
- [ ] Animations
- [ ] Micro-interactions
- [ ] Accessibility testing
- [ ] Performance optimization
- [ ] Browser testing

## Inspiration References

- **Vercel Dashboard**: Clean layout, subtle animations
- **Linear**: Minimal design, excellent typography
- **Raycast**: Keyboard-first, efficient workflows
- **GitHub**: Familiar patterns, clear hierarchy
- **Figma**: Professional tools, intuitive controls
