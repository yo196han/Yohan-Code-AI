---
name: fullstack-coding
version: "1.0.0"
description: >
  Professional full-stack web development skill. Triggers on any request involving
  code generation, web application building, UI/UX design, frontend frameworks (React, Vue, 
  Svelte, Angular), backend APIs (Node.js, Python, Go, Rust), databases, CSS/styling, 
  component design, layout systems, or interactive features. Covers architecture, responsive 
  design, accessibility (a11y), performance, state management, API design, and deployment.

  Keywords: code, build, app, website, web app, full stack, frontend, backend, API, database,
  React, Vue, Next.js, Nuxt, CSS, HTML, JavaScript, TypeScript, UI, UX, component, layout,
  form, dashboard, landing page, SPA, SSR, REST, GraphQL, SQL, NoSQL, auth, deploy.
---

# Full-Stack Professional Coding

## Philosophy

Write **production-grade code** — not demos. Every output must be:
- **Accessible** (WCAG 2.1 AA minimum)
- **Responsive** (mobile-first, fluid breakpoints)
- **Performant** (minimal re-renders, lazy loading, optimized assets)
- **Type-safe** (TypeScript by default unless explicitly requested otherwise)
- **Maintainable** (clear naming, single responsibility, composable)
- **Beautiful** (thoughtful spacing, hierarchy, motion, and micro-interactions)

## Trigger Conditions

Activate this skill when the user:
- Requests code, a website, web app, or any software build
- Mentions any framework, library, or tech stack
- Asks for UI/UX improvements, redesigns, or component creation
- Discusses architecture, database design, or API structure
- Needs help debugging, refactoring, or optimizing code
- Wants a dashboard, form, landing page, e-commerce, SaaS, or any web interface

## Workflow

### 1. Discovery & Scoping (Mental Model)
Before writing code, establish:
- **User goal**: What is the user trying to accomplish?
- **Audience**: Who will use this? (technical vs. non-technical, mobile vs. desktop)
- **Scope**: MVP features vs. nice-to-have. Do not over-engineer.
- **Tech stack**: Infer from context or ask. Default modern stack:
  - Frontend: **React 18+ + TypeScript + Tailwind CSS**
  - Backend: **Node.js/Express or Python/FastAPI**
  - Database: **PostgreSQL** (relational) or **MongoDB** (document)
  - Auth: **JWT + bcrypt** (simple) or **OAuth2/OIDC** (enterprise)
  - Deployment: **Vercel/Netlify** (frontend), **Railway/Render** (backend)

### 2. Architecture First
- Draw the data flow and component tree mentally
- Separate concerns: UI layer → State layer → API layer → Data layer
- Choose state management: 
  - Simple: React Context + useReducer
  - Complex: Zustand, Jotai, or Redux Toolkit
  - Server state: TanStack Query (React Query) or SWR
- Plan the API contract (OpenAPI/Swagger style) before implementation

### 3. UX/UI Design System
Read the **UX/UI Patterns** section below before implementing any UI.

**Mandatory checks for every UI:**
- [ ] Color contrast ratio ≥ 4.5:1 for normal text, 3:1 for large text
- [ ] Focus indicators visible and styled (never `outline: none` without replacement)
- [ ] Touch targets ≥ 44×44px on mobile
- [ ] Labels linked to inputs via `htmlFor` + `id`
- [ ] Alt text for all images, `aria-label` for icon-only buttons
- [ ] Reduced motion support: `@media (prefers-reduced-motion: reduce)`
- [ ] Semantic HTML: `<header>`, `<main>`, `<nav>`, `<article>`, `<section>`, `<footer>`
- [ ] Heading hierarchy: exactly one `<h1>`, no skipped levels
- [ ] Form validation: inline, immediate, with clear error messages
- [ ] Loading states for every async operation
- [ ] Empty states for lists, search results, and dashboards
- [ ] Error boundaries and fallback UIs

### 4. Component Structure
Follow this file organization:
```
components/
  ui/              # Primitive, reusable atoms (Button, Input, Card, Badge)
  forms/           # Form-specific molecules (LoginForm, SearchBar)
  layout/          # Structural components (Navbar, Sidebar, Footer, Grid)
  features/        # Domain-specific organisms (UserProfile, OrderList)
  pages/           # Page-level compositions (HomePage, DashboardPage)
```

**Component rules:**
- Props interface always defined and exported
- Default props for optional values
- Composition over configuration (render props / slots pattern)
- No prop drilling beyond 2 levels — use context or state management
- Co-locate styles, tests, and stories with components

### 5. Styling Rules
- **Mobile-first**: Base styles for mobile, `md:` and `lg:` breakpoints for larger screens
- **Design tokens**: Use CSS variables or Tailwind config for colors, spacing, typography
- **Consistent spacing**: 4px base unit (0.25rem). Use `gap`, `padding`, `margin` from scale
- **Typography**: Max 2 font families. Line-height 1.5 for body, 1.2 for headings
- **Shadows & depth**: Use sparingly. Prefer `shadow-sm` and `shadow-md`. Never `shadow-2xl` on everything
- **Borders & radius**: Consistent radius scale (sm: 4px, md: 8px, lg: 12px, xl: 16px, full: 9999px)
- **Transitions**: 150ms–300ms, `ease-in-out` or `cubic-bezier(0.4, 0, 0.2, 1)`

### 6. Code Quality
- **TypeScript**: Strict mode. No `any`. Use `unknown` with type guards.
- **Naming**: 
  - Components: PascalCase (`UserCard`)
  - Hooks: camelCase starting with `use` (`useAuth`)
  - Utils: camelCase (`formatDate`)
  - Constants: UPPER_SNAKE_CASE (`API_BASE_URL`)
  - Files: match default export name
- **Functions**: Pure when possible. Max 20 lines. Single responsibility.
- **Error handling**: Never swallow errors. Always log and show user-friendly messages.
- **Async**: Use `async/await`. Handle loading, error, and success states explicitly.

### 7. Backend & API
- RESTful or GraphQL with clear schema
- Input validation (Zod, Joi, or class-validator)
- Rate limiting and CORS configuration
- Environment variables for secrets (never commit `.env`)
- Structured logging (Winston, Pino)
- Database: migrations for schema changes, indexes for query performance
- Auth: HTTP-only cookies for sessions, `Secure` and `SameSite` flags

### 8. Performance
- Code-splitting with `React.lazy()` and `Suspense`
- Image optimization: WebP/AVIF, `loading="lazy"`, `srcset`
- Font optimization: `font-display: swap`, subsetting, preconnect
- Debounce/throttle: search inputs (300ms), scroll handlers (16ms)
- Memoization: `React.memo`, `useMemo`, `useCallback` — but only when profiling shows need
- Bundle analysis: Check for duplicate dependencies

### 9. Security
- Sanitize all user inputs (DOMPurify for HTML, parameterized queries for SQL)
- CSP headers configured
- HTTPS only
- Dependency scanning (`npm audit`, Snyk)
- No secrets in client-side code

### 10. Delivery
- Provide complete, runnable code — not snippets
- Include `README.md` with setup instructions
- Include environment variable template (`.env.example`)
- If the code is long, split into logical files
- Add comments for complex logic, not for obvious code
- Include a "What I Built" summary and "Next Steps" section

## Response Format

```
## What I Built
Brief summary of the application/feature and the tech stack used.

## Architecture
[Component tree or data flow diagram in ASCII/text]

## File Structure
```
project/
├── src/
│   ├── components/
│   ├── hooks/
│   ├── lib/
│   ├── types/
│   └── app.tsx
├── package.json
└── README.md
```

## Code
[Complete, copy-paste ready code blocks]

## UX/UI Decisions
- Why I chose this layout
- Accessibility features included
- Responsive behavior
- Animation/motion rationale

## Next Steps
- Suggested improvements
- Deployment instructions
- Testing strategy
```

---

# Reference: UX/UI Patterns

## Design Principles

### 1. Visual Hierarchy
- **Size**: Larger elements draw more attention. Headings should scale predictably.
- **Weight**: Bold for emphasis, regular for body. Max 3 weights per interface.
- **Color**: Use color sparingly for actions and states. Neutral grays for structure.
- **Spacing**: White space is not empty space — it is active design. Group related items.
- **Contrast**: Ensure text is readable against backgrounds. Use contrast checkers.

### 2. The 8-Point Grid System
All spacing, sizing, and positioning should align to an 8px base unit:
- `4px` (0.25rem): Tight gaps, icon padding
- `8px` (0.5rem): Default inline spacing
- `16px` (1rem): Standard padding, gap between related items
- `24px` (1.5rem): Section separation
- `32px` (2rem): Major section breaks
- `48px` (3rem): Page-level spacing
- `64px` (4rem): Hero/large section padding

### 3. Z-Index Scale
Never use arbitrary z-index values. Use a defined scale:
```
z-0:   Base layer (backgrounds)
z-10:  Content cards
z-20:  Sticky headers
z-30:  Dropdown menus
z-40:  Modals/dialog overlays
z-50:  Toasts/notifications
z-auto: Default stacking
```

### 4. Color System
Use a structured palette:
```
Primary:    Brand color for CTAs, links, active states
Secondary:  Complementary actions, tags
Success:    Positive feedback, completed states
Warning:    Caution, pending states
Danger:     Errors, destructive actions
Info:       Neutral highlights, tips

Neutrals:
- bg-primary:   Main background
- bg-secondary: Card/surface background
- bg-tertiary:  Hover states, subtle backgrounds
- text-primary: Headings, primary content
- text-secondary: Body text, descriptions
- text-tertiary:  Placeholders, disabled text
- border:       Dividers, outlines
```

### 5. Typography Scale
```
Display:   48px / 1.1 / -0.02em / 700  (Hero headlines)
H1:        36px / 1.2 / -0.01em / 700  (Page titles)
H2:        30px / 1.2 / 0em / 600      (Section headers)
H3:        24px / 1.3 / 0em / 600      (Subsection headers)
H4:        20px / 1.4 / 0em / 500      (Card titles)
H5:        18px / 1.4 / 0em / 500      (Small headers)
Body:      16px / 1.6 / 0em / 400      (Main content)
Body-sm:   14px / 1.5 / 0em / 400      (Secondary content)
Caption:   12px / 1.4 / 0.01em / 400   (Labels, metadata)
```

### 6. Common Layout Patterns

#### Dashboard
```
┌─────────────────────────────────────┐
│  Sidebar │  Header                  │
│          ├──────────────────────────┤
│          │  Stats Cards (grid)      │
│          ├──────────────────────────┤
│          │  Main Content Area       │
│          │  (table / chart / list)  │
│          │                          │
└─────────────────────────────────────┘
```
- Sidebar: 240–280px fixed, collapsible on mobile
- Header: 64px fixed, z-20
- Stats: 3–4 cards in responsive grid (1 col mobile, 2 tablet, 4 desktop)
- Content: scrollable, max-width 1400px centered

#### Landing Page
```
┌─────────────────────────────────────┐
│  Navbar (fixed, transparent→solid)  │
├─────────────────────────────────────┤
│  Hero Section (full viewport)       │
├─────────────────────────────────────┤
│  Features Grid (3-col)              │
├─────────────────────────────────────┤
│  Social Proof / Testimonials        │
├─────────────────────────────────────┤
│  CTA Section                        │
├─────────────────────────────────────┤
│  Footer (4-col links + social)      │
└─────────────────────────────────────┘
```

#### Form Layout
- Max width: 480px for single-column, 640px for multi-column
- Label above input (not inline)
- Helper text below input
- Error message in red, with icon
- Submit button full-width on mobile, auto on desktop
- Group related fields with fieldsets

### 7. Micro-Interactions

#### Hover States
- Buttons: `brightness(1.1)` or subtle background shift, 150ms transition
- Cards: `translateY(-2px)` + `shadow-md`, 200ms ease-out
- Links: Underline animation (width 0→100%) or color shift
- Images: `scale(1.02)` with overflow hidden on container

#### Focus States
- Visible ring: `ring-2 ring-primary ring-offset-2`
- Never remove outline without replacement
- Focus-visible only (not on mouse click)

#### Loading States
- Buttons: Spinner icon replaces text, disabled state
- Cards: Skeleton screens (shimmer animation)
- Pages: Progress bar at top or centered spinner
- Content: Inline spinner for async sections

#### Empty States
- Illustration + headline + description + CTA button
- Never show a blank screen
- Example: "No orders yet" + "Start shopping" button

### 8. Motion Principles
- **Duration**: 150ms for micro-interactions, 300ms for transitions, 500ms for page changes
- **Easing**: 
  - Default: `cubic-bezier(0.4, 0, 0.2, 1)` (ease-out)
  - Enter: `cubic-bezier(0, 0, 0.2, 1)` (decelerate)
  - Exit: `cubic-bezier(0.4, 0, 1, 1)` (accelerate)
- **Principles**: 
  - Motion should guide attention, not distract
  - Elements entering: fade + slight translateY(8px→0)
  - Elements exiting: fade out quickly
  - Stagger children by 50ms for lists
- **Respect `prefers-reduced-motion`**: Disable animations for users who prefer reduced motion

### 9. Dark Mode
- Use `dark:` Tailwind prefixes or CSS variables
- Never invert colors with `filter: invert(1)`
- Adjust shadows: lighter shadows in dark mode
- Adjust borders: use subtle borders instead of shadows for depth
- Test all color combinations in both modes

### 10. Responsive Breakpoints
```
Mobile:     < 640px   (default, single column)
Tablet:     ≥ 640px   (sm:)
Desktop:    ≥ 768px   (md:)
Large:      ≥ 1024px  (lg:)
XL:         ≥ 1280px  (xl:)
2XL:        ≥ 1536px  (2xl:)
```
- Design mobile-first: start with mobile layout, enhance for larger screens
- Touch targets: min 44×44px on mobile
- Font sizes: slightly larger on mobile for readability (16px minimum to prevent iOS zoom)
- Navigation: hamburger menu on mobile, horizontal nav on desktop

---

# Reference: Architecture Patterns

## Frontend Architecture

### 1. Component Architecture: Atomic Design
```
Atoms:       Button, Input, Label, Icon, Badge
Molecules:   SearchBar (Input + Button + Icon), FormField (Label + Input + Error)
Organisms:   Navbar (Logo + NavLinks + SearchBar + UserMenu), ProductCard
Templates:   Page layouts with placeholder content
Pages:       Actual pages composed of organisms
```

### 2. State Management Decision Tree
```
Local UI state only?                    → useState / useReducer
Shared across few components?           → React Context + useReducer
Server data (fetch/cache/update)?       → TanStack Query (React Query)
Complex client state (filters, forms)?  → Zustand or Jotai
Time-travel debugging needed?           → Redux Toolkit
```

### 3. Folder Structure (Modern React)
```
src/
├── app/                    # Next.js App Router or main app entry
│   ├── layout.tsx
│   ├── page.tsx
│   └── globals.css
├── components/
│   ├── ui/                 # Primitive shadcn/ui style components
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── card.tsx
│   │   └── dialog.tsx
│   ├── forms/              # Form molecules
│   ├── layout/             # Navbar, Sidebar, Footer
│   └── features/           # Domain-specific (UserProfile, OrderList)
├── hooks/                  # Custom React hooks
│   ├── useAuth.ts
│   ├── useLocalStorage.ts
│   └── useDebounce.ts
├── lib/                    # Utilities, configs, API clients
│   ├── utils.ts            # cn() helper, formatters
│   ├── api.ts              # Axios/fetch wrapper
│   └── constants.ts
├── types/                  # Global TypeScript types
│   ├── user.ts
│   └── api.ts
├── stores/                 # Zustand/Jotai state stores
├── styles/                 # Global styles, CSS variables
└── public/                 # Static assets
```

### 4. API Layer Pattern
```typescript
// lib/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor: attach auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Response interceptor: handle errors globally
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

export default api;
```

### 5. Data Fetching Pattern (TanStack Query)
```typescript
// hooks/useUsers.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

export function useUsers() {
  return useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const { data } = await api.get('/users');
      return data;
    },
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (user: UserCreate) => api.post('/users', user),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
}
```

### 6. Form Handling Pattern (React Hook Form + Zod)
```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
});

type FormData = z.infer<typeof schema>;

function LoginForm() {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    await login(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('email')} />
      {errors.email && <span>{errors.email.message}</span>}
      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Loading...' : 'Login'}
      </button>
    </form>
  );
}
```

## Backend Architecture

### 1. Layered Architecture
```
Presentation Layer  → Controllers / Routes
Business Layer      → Services / Use Cases
Data Layer          → Repositories / Models
```
- Controllers: Handle HTTP, validate input, delegate to services
- Services: Business logic, orchestration, rules
- Repositories: Database access, query optimization

### 2. RESTful API Design
```
GET    /api/users              → List users (paginated)
GET    /api/users/:id          → Get single user
POST   /api/users              → Create user
PUT    /api/users/:id          → Full update
PATCH  /api/users/:id          → Partial update
DELETE /api/users/:id          → Delete user
GET    /api/users/:id/orders   → Nested resource
```

### 3. Response Standardization
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 150
  }
}
```

### 4. Error Handling
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      { "field": "email", "message": "Email is required" }
    ]
  }
}
```

### 5. Authentication Flow (JWT)
```
1. Client POST /auth/login { email, password }
2. Server validates → generates JWT (access + refresh tokens)
3. Access token: short-lived (15 min), stored in memory
4. Refresh token: long-lived (7 days), HTTP-only cookie
5. Client sends access token in Authorization header
6. On 401, client uses refresh token to get new access token
7. On logout, invalidate refresh token server-side
```

### 6. Database Patterns
- **One-to-Many**: User → Posts (foreign key on posts table)
- **Many-to-Many**: Users ↔ Roles (junction table user_roles)
- **Soft Deletes**: `deleted_at` timestamp instead of hard delete
- **Timestamps**: `created_at`, `updated_at` on every table
- **Indexing**: Index foreign keys, search fields, and sort columns
- **Migrations**: Version-controlled schema changes (never modify prod DB manually)

---

# Reference: Component Library

## Primitive Components

### Button
```typescript
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  onClick?: () => void;
  children: React.ReactNode;
}
```
- Primary: solid brand color, white text
- Secondary: subtle background, brand text
- Ghost: transparent, hover background
- Danger: red background for destructive actions
- Outline: bordered, transparent background
- Loading state: spinner replaces text, disabled
- Disabled: opacity 0.5, no-pointer-events

### Input
```typescript
interface InputProps {
  type?: 'text' | 'email' | 'password' | 'number' | 'search';
  label?: string;
  placeholder?: string;
  error?: string;
  helperText?: string;
  required?: boolean;
  disabled?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}
```
- Label always above input (not placeholder-as-label)
- Error message below with red text + icon
- Helper text in muted color
- Focus ring on focus
- Invalid state: red border + icon

### Card
```typescript
interface CardProps {
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  hoverable?: boolean;
  clickable?: boolean;
  className?: string;
}
```
- Consistent padding (24px default, 16px compact)
- Subtle border or shadow for elevation
- Optional header with title/subtitle
- Optional footer (actions, metadata)
- Hoverable: lift effect on hover
- Clickable: cursor pointer, focus ring

### Badge
```typescript
interface BadgeProps {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info';
  size?: 'sm' | 'md';
  children: React.ReactNode;
}
```
- Small pill-shaped label
- Color-coded by semantic meaning
- Used for status, categories, counts

### Dialog / Modal
```typescript
interface DialogProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}
```
- Backdrop blur + dark overlay
- Focus trap inside modal
- Close on Escape key, backdrop click
- Enter/Exit animations (fade + scale)
- Scroll lock on body when open

### Toast / Notification
```typescript
interface ToastProps {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
  onClose: (id: string) => void;
}
```
- Position: top-right or bottom-right
- Auto-dismiss with progress bar
- Stacked with 8px gap
- Icon + color by type
- Action button support (Undo, View)

## Form Components

### Select / Dropdown
- Native select for simple cases
- Custom dropdown for search, multi-select, async
- Keyboard navigation (arrow keys, Enter, Escape)
- Clear button for nullable selects

### Checkbox & Radio
- Custom styled but accessible (hidden native input)
- Grouped with fieldset + legend
- Indeterminate state for parent checkboxes
- Inline or stacked layout

### Toggle / Switch
- Clear on/off visual state
- Label on right or left
- Smooth 200ms transition
- Accessible: role="switch", aria-checked

### Date Picker
- Calendar grid with keyboard navigation
- Range selection support
- Min/max date constraints
- Mobile: native date input fallback

## Layout Components

### Navbar
- Fixed top, height 64px
- Logo left, nav links center, actions right
- Mobile: hamburger menu with slide-in drawer
- Scroll behavior: transparent → solid background
- Active link indicator

### Sidebar
- Width 240–280px, fixed left
- Collapsible with hamburger toggle
- Nested navigation with accordions
- Active item highlight
- Mobile: overlay drawer

### Grid
```typescript
interface GridProps {
  cols?: 1 | 2 | 3 | 4 | 5 | 6;
  gap?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
}
```
- Responsive: 1 col mobile, 2 tablet, 3+ desktop
- Consistent gap spacing
- Auto-fit for card grids

### Container
- Max-width: 640px (sm), 768px (md), 1024px (lg), 1280px (xl)
- Centered with auto margins
- Padding: 16px mobile, 24px desktop

## Data Display

### Table
- Sortable columns with arrow indicators
- Pagination or infinite scroll
- Row hover highlight
- Empty state
- Loading skeleton
- Sticky header on scroll
- Responsive: card layout on mobile

### Tabs
- Horizontal or vertical
- Active indicator (underline or background)
- Keyboard navigation (arrow keys)
- Lazy loading of tab content

### Accordion
- One item open at a time (default) or multiple
- Smooth height animation
- Chevron icon rotation
- Keyboard: Enter to toggle, arrow keys to navigate

### Tooltip
- Delayed show (300ms), instant hide
- Position: auto (top/bottom/left/right)
- Dark background, white text
- Never cover the trigger element
- Accessible: aria-describedby

### Skeleton
- Animated shimmer (gradient sweep)
- Match the shape of the content being loaded
- Use for cards, text blocks, avatars, tables
- Never use spinner for content layout

---

# Reference: Accessibility (a11y) Checklist

## WCAG 2.1 AA Compliance Checklist

### Perceivable

#### 1.1 Text Alternatives
- [ ] All images have meaningful `alt` text
  - Decorative images: `alt=""` (empty)
  - Informative images: descriptive alt
  - Functional images (buttons): describe action, not appearance
  - Complex images (charts): provide detailed description nearby
- [ ] Icons without visible text have `aria-label`
- [ ] Videos have captions, transcripts, and audio descriptions
- [ ] Audio content has transcripts

#### 1.2 Color & Contrast
- [ ] Text contrast ratio ≥ 4.5:1 for normal text (< 18pt)
- [ ] Text contrast ratio ≥ 3:1 for large text (≥ 18pt bold or 24pt)
- [ ] UI components (buttons, form borders) contrast ≥ 3:1 against adjacent colors
- [ ] Information is not conveyed by color alone (use icons + text + color)
- [ ] Links are distinguishable from surrounding text (underline or sufficient contrast)

#### 1.3 Resize & Reflow
- [ ] Content readable at 200% zoom without horizontal scrolling
- [ ] Content readable at 400% zoom (320px viewport width)
- [ ] Text spacing can be overridden without breaking layout
- [ ] No loss of content or functionality when zooming

### Operable

#### 2.1 Keyboard Navigation
- [ ] All interactive elements reachable via Tab key
- [ ] Tab order follows logical reading order (top-to-bottom, left-to-right)
- [ ] No keyboard traps (user can Tab out of any component)
- [ ] Skip link provided to bypass repetitive navigation
- [ ] Custom components have keyboard handlers:
  - Dropdown: Arrow keys, Enter, Escape, Tab
  - Modal: Tab trap, Escape to close
  - Tabs: Arrow keys to switch
  - Accordion: Enter/Space to toggle, arrow keys to navigate

#### 2.2 Focus Management
- [ ] Focus indicator is visible on all interactive elements
- [ ] Focus indicator has sufficient contrast (3:1 against background)
- [ ] Focus returns to trigger element when modal/dialog closes
- [ ] Focus moves to error messages when form submission fails
- [ ] No `outline: none` without replacement focus style
- [ ] Focus style: `ring-2 ring-primary ring-offset-2` or equivalent

#### 2.3 Time & Motion
- [ ] No auto-playing content without pause/stop control
- [ ] Users can extend or disable session timeouts
- [ ] Animations respect `prefers-reduced-motion: reduce`
- [ ] No flashing content > 3 times per second

### Understandable

#### 3.1 Forms & Input
- [ ] All form inputs have associated `<label>` (linked via `htmlFor` + `id`)
- [ ] Required fields indicated visually and programmatically (`aria-required`)
- [ ] Input purpose identifiable (autocomplete attributes)
- [ ] Error messages:
  - Associated with input via `aria-describedby` or `aria-errormessage`
  - Clear and specific ("Email must contain @ symbol" not "Invalid input")
  - Visible near the field, not just in a toast
- [ ] Form submission errors summarized at top of form
- [ ] No unexpected form submission on Enter (except single-field forms)

#### 3.2 Navigation & Structure
- [ ] Page has exactly one `<h1>` heading
- [ ] Heading hierarchy is logical (no skipped levels: h1 → h2 → h3)
- [ ] Landmark regions used: `<header>`, `<nav>`, `<main>`, `<aside>`, `<footer>`
- [ ] Page title (`<title>`) is unique and descriptive
- [ ] Breadcrumb navigation for multi-level pages
- [ ] Current page indicated in navigation (`aria-current="page"`)

#### 3.3 Language & Reading
- [ ] HTML `lang` attribute set correctly (e.g., `lang="en"`)
- [ ] Language changes within content marked with `lang` attribute
- [ ] Reading order matches visual order (CSS does not disrupt tab/screen reader order)

### Robust

#### 4.1 ARIA Usage
- [ ] Native HTML elements preferred over ARIA when possible
- [ ] ARIA roles used correctly:
  - `role="button"` only on elements that act like buttons
  - `role="dialog"` for modals with `aria-modal="true"`
  - `role="alert"` for error messages
  - `role="status"` for success/loading messages
- [ ] Dynamic content updates announced to screen readers:
  - `aria-live="polite"` for non-critical updates
  - `aria-live="assertive"` for critical errors
- [ ] `aria-expanded` on expandable components (accordions, dropdowns)
- [ ] `aria-hidden="true"` on decorative elements only
- [ ] No `aria-hidden` on focusable elements

#### 4.2 Screen Reader Testing
- [ ] Test with at least one screen reader (NVDA, JAWS, VoiceOver)
- [ ] Interactive elements announce their purpose and state
- [ ] Dynamic content (toasts, modals) is announced
- [ ] Tables announce headers with data cells
- [ ] Form errors read when navigating to invalid field

## Common A11y Anti-Patterns to Avoid

❌ **Div buttons**: `<div onClick={...}>` — use `<button>`
❌ **Missing labels**: `<input placeholder="Email">` — use `<label>`
❌ **Placeholder as label**: Placeholders disappear on input
❌ **Icon-only buttons without aria-label**: Screen readers announce "button" with no context
❌ **Modal without focus trap**: Tab escapes to background content
❌ **Color-only error indication**: Red border without text or icon
❌ **Auto-playing carousels**: No pause/stop control
❌ **Missing skip links**: Keyboard users must tab through all nav items
❌ **Non-semantic headings**: Using `<div className="h1">` instead of `<h1>`
❌ **Table layout for non-tabular data**: Use CSS Grid/Flexbox instead

## Quick A11y Audit Commands

```bash
# Install axe-core for automated testing
npm install @axe-core/react

# Chrome DevTools Lighthouse → Accessibility score should be 100
# Firefox Accessibility Inspector → Check contrast and keyboard
# WAVE Extension → Visual overlay of a11y issues
```

---

# Reference: Performance Guide

## Frontend Performance

### 1. Loading Performance (Core Web Vitals)

#### Largest Contentful Paint (LCP) — Target: < 2.5s
- [ ] Preload critical resources: `<link rel="preload">` for hero image, critical CSS
- [ ] Optimize images: WebP/AVIF format, proper sizing, `srcset` for responsive
- [ ] Remove render-blocking resources: inline critical CSS, defer non-critical JS
- [ ] Use a CDN for static assets
- [ ] Server-side rendering (SSR) or static generation (SSG) for initial HTML
- [ ] Font optimization: `font-display: swap`, preload critical fonts, use system font stack as fallback

#### First Input Delay (FID) / Interaction to Next Paint (INP) — Target: < 200ms
- [ ] Break up long tasks (> 50ms) using `setTimeout` or `requestIdleCallback`
- [ ] Defer non-critical JavaScript with `defer` or `async`
- [ ] Use Web Workers for heavy computation
- [ ] Minimize main thread work: avoid large DOM manipulations
- [ ] Virtualize long lists (react-window, react-virtualized)

#### Cumulative Layout Shift (CLS) — Target: < 0.1
- [ ] Always set `width` and `height` on images and videos
- [ ] Reserve space for ads, embeds, and dynamic content
- [ ] Never insert content above existing content (except in response to user interaction)
- [ ] Use `transform` animations instead of layout-triggering properties (width, height, top, left)
- [ ] Load web fonts without causing FOUT (flash of unstyled text)

### 2. Bundle Optimization
- [ ] Code splitting: `React.lazy()` + `Suspense` for routes and heavy components
- [ ] Tree shaking: use ES modules (`import/export`), avoid side-effect imports
- [ ] Dynamic imports: `import('./HeavyComponent')` for on-demand loading
- [ ] Remove unused dependencies (`depcheck`, `npm-check`)
- [ ] Analyze bundle: `webpack-bundle-analyzer` or `@next/bundle-analyzer`
- [ ] Choose lightweight libraries: date-fns over moment, zustand over redux (if simple)
- [ ] Polyfills only for target browsers (use `browserslist`)

### 3. Image Optimization
```html
<!-- Responsive images -->
<img
  src="image-400.webp"
  srcset="image-400.webp 400w, image-800.webp 800w, image-1200.webp 1200w"
  sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
  alt="Description"
  loading="lazy"
  decoding="async"
/>
```
- Use Next.js `<Image>` component (automatic optimization)
- Serve WebP/AVIF with JPEG fallback
- Lazy load below-the-fold images
- Use CSS `aspect-ratio` to prevent layout shift
- Compress images: TinyPNG, Squoosh, or build-time optimization

### 4. CSS Performance
- [ ] Avoid deep nesting (max 3 levels)
- [ ] Prefer class selectors over tag or universal selectors
- [ ] Use `contain: layout` for isolated components
- [ ] Animate only `transform` and `opacity` (GPU-accelerated)
- [ ] Remove unused CSS (PurgeCSS, Tailwind JIT mode)
- [ ] Critical CSS inlined, rest loaded asynchronously

### 5. JavaScript Runtime
- [ ] Memoization: `React.memo`, `useMemo`, `useCallback` — measure first, optimize second
- [ ] Virtual scrolling for lists > 50 items
- [ ] Debounce: search inputs (300ms), resize handlers (100ms)
- [ ] Throttle: scroll handlers (16ms = 60fps), mouse move
- [ ] Avoid `useEffect` for derived state — compute during render
- [ ] Use `useRef` for values that do not trigger re-renders
- [ ] State colocation: keep state as close to where it is used as possible

### 6. Caching Strategy
```
Static assets (JS, CSS, images):   Cache-Control: public, max-age=31536000, immutable
HTML pages:                        Cache-Control: no-cache (revalidate)
API responses (rarely changing):   Cache-Control: public, max-age=3600
API responses (frequently changing): Cache-Control: no-cache
```
- Service Worker for offline support and aggressive caching
- Stale-while-revalidate pattern for instant UI updates

## Backend Performance

### 1. Database Optimization
- [ ] Index foreign keys, search fields, and sort columns
- [ ] Use `EXPLAIN ANALYZE` to check query performance
- [ ] N+1 query prevention: eager loading (JOINs) or data loader pattern
- [ ] Pagination: cursor-based for real-time, offset-based for static
- [ ] Connection pooling (PgBouncer for PostgreSQL)
- [ ] Read replicas for read-heavy workloads
- [ ] Cache frequent queries (Redis, Memcached)

### 2. API Performance
- [ ] Response compression: gzip or brotli
- [ ] HTTP/2 or HTTP/3 for multiplexing
- [ ] Rate limiting to prevent abuse
- [ ] Request validation at edge (middleware) before business logic
- [ ] Batch endpoints for multiple operations
- [ ] GraphQL: query complexity analysis and depth limiting

### 3. Server & Infrastructure
- [ ] Horizontal scaling: load balancer + multiple app instances
- [ ] Vertical scaling: more CPU/RAM for compute-heavy tasks
- [ ] Containerization: Docker for consistent environments
- [ ] CDN for static assets and edge caching
- [ ] Serverless for variable traffic (AWS Lambda, Vercel Functions)
- [ ] Health checks and graceful shutdowns

## Performance Budget
Set targets and enforce them:
```
JavaScript:     < 200 KB (gzipped) initial load
CSS:            < 50 KB (gzipped) initial load
Images:         < 500 KB total on initial viewport
Fonts:          < 100 KB, max 2 font families
LCP:            < 2.5 seconds
INP:            < 200 milliseconds
CLS:            < 0.1
Time to Interactive: < 3.5 seconds
```

## Performance Testing Tools
- **Lighthouse**: Chrome DevTools automated audit
- **WebPageTest**: Detailed waterfall analysis
- **GTmetrix**: Page speed monitoring
- **Calibre**: Continuous performance monitoring
- **SpeedCurve**: RUM (Real User Monitoring) + synthetic testing
- **Chrome DevTools Performance Panel**: Flame charts, long tasks
- **React DevTools Profiler**: Component render times

---

## System Reminders

<SYSTEM_REMINDER awareness="high">
- Always write TypeScript, not plain JavaScript, unless the user explicitly requests JS.
- Always use semantic HTML and ARIA labels where needed.
- Never provide incomplete code — if the output is long, split into multiple messages or files.
- When building a UI, always consider dark mode support (use `dark:` Tailwind variants or CSS variables).
- Test your mental model: "Would a junior developer understand this structure?"
- Before implementing any UI, review the UX/UI Patterns section for design tokens, spacing, and motion rules.
- Before designing system architecture, review the Architecture Patterns section for folder structure and state management decisions.
- Before declaring a UI complete, run through the Accessibility Checklist.
- Before finalizing code, review the Performance Guide for optimization opportunities.
</SYSTEM_REMINDER>
