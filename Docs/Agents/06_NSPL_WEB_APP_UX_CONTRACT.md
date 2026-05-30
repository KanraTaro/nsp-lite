# NSPL Web App UX Contract

## Purpose

This document defines the UX contract for NSPL Web apps.

It exists because an app can be architecturally correct and still feel terrible.

LifeRPG proved this directly: Codex successfully added Core services, Skills, and HTMX routes, but the first management UI became a raw CRUD wall that technically worked while failing the product experience.

This contract prevents that pattern from spreading to RohTalk Web, DST dashboards, Video Web tools, future business apps, and any new NSPL Web app.

## Prime Rule

NSPL Web apps are not raw admin consoles.

They are command surfaces.

A Web app should help the user understand what is happening, choose the next action, and trust that the system updated correctly.

## Board vs Management

### Boards / Dashboards

A Board is the default command surface.

It should show:

- current status
- next action
- important summaries
- active work
- recent changes
- compact previews
- clear navigation
- meaningful feedback

A Board should not show:

- every object
- every edit field
- raw JSON
- giant forms
- CRUD controls for every item
- internal implementation details

### Management Pages

Management pages are where users create, edit, archive, reorder, and inspect objects.

They can have forms, but they should still avoid visual overload.

Common examples:

- Inbox management
- Quest management
- Habit management
- Event management
- Settings
- Provider connections
- Tool configuration

## Progressive Disclosure

Do not show everything at once.

Default views should use compact cards or rows.

Show detail/edit controls only when requested.

Acceptable patterns:

- `Edit` button reveals one item form
- `Details` section expands one item
- `Add` button reveals a create form
- summary cards link to full management pages
- advanced fields collapsed under “Advanced”

Avoid:

- always-visible edit forms for every item
- repeated full forms in every card
- unbounded lists on dashboards
- raw data dumps as primary UI

## Enum Fields Use Selects

If a field has known values, use a select, checkbox, radio group, or constrained control.

Do not use free-text boxes for enum-like fields.

Examples:

- Categories: Survival, Build, Family, Home, Body, Admin, Joy, Recovery, Social, Errands
- Habit cadence: daily, weekdays, weekly, monthly, custom
- Quest status: open, active, paused, completed, archived
- Event status: scheduled, active, complete, archived
- Reward intensity: low, normal, high
- Strictness mode: gentle, balanced, hard, custom
- Visual mode: command_center, compact, mobile

If the field is truly open-ended, a text input is fine.

## Settings Must Be Real

Do not show fake settings as if they are active.

A setting should either:

1. visibly affect the app,
2. affect future behavior,
3. be clearly labeled as future/deferred,
4. be hidden until implemented.

Examples of real settings:

- `display_name` appears in the UI
- `auto_sort_enabled` changes Quick Dump behavior
- `checkin_minutes` influences quest session timeout
- `visual_mode` adds a CSS/layout class

Bad pattern:

- saving settings to disk but never using them anywhere

## HTMX Rules

HTMX is a good fit for NSPL Web apps, but only with discipline.

### Stable Panel IDs

Full-panel partials should have stable IDs.

Example:

```html
<section id="habit-panel" class="panel">
  ...
</section>
```

### outerHTML for Full Panel Replacement

If an endpoint returns a full panel wrapper, use:

```html
hx-target="#habit-panel"
hx-swap="outerHTML"
```

Do not rely on default `innerHTML` for full panel returns.

### Avoid closest section for Full Panels

Avoid:

```html
hx-target="closest section"
```

when returning full panel wrappers. It can easily nest panels inside themselves.

### Out-of-Band Updates

When one action affects multiple panels, use HTMX out-of-band swaps where practical.

Starting a quest may need to update active session, expedition, quest preview, inbox preview, and Roh actions panels.

Completing a quest may need to update active session, expedition, rewards, quest list, and recent log.

The UI should not feel stale after an action.

### Test HTMX Contracts

Tests should verify:

- expected stable IDs exist
- full-panel triggers use `outerHTML`
- unsafe nesting patterns do not return
- important actions update expected panels
- settings/actions produce user-visible changes

Do not only test “route returns 200.”

## Plain JavaScript Rules

Plain JavaScript is acceptable for opening/closing lightweight panels, reward popups, small animations, button disable/enable, periodic refresh, keyboard shortcuts, tiny client-side UI state, and drag/reorder later.

Plain JS should not become a hidden app state layer, a second source of truth, an untested mini-framework, or a replacement for durable NodeCTX state.

If behavior becomes complex, consider extracting a reusable NSPL Web helper pattern.

## CSS and Visual Feedback

Visual polish is functional.

For users with ADHD-like friction, motivation issues, or game-oriented brains, UI feedback can be the difference between using the app and abandoning it.

NSPL apps should use visual feedback deliberately:

- progress bars
- pulses
- badges
- reward flashes
- card state changes
- clear completed/active/blocked styling
- visible command confirmations
- compact but meaningful status chips
- readable mobile layouts

Avoid flat walls of text, tiny unlabeled controls, unstyled form dumps, unclear success/failure states, and hiding important status changes.

## Mobile Matters

NSPL Web apps should be usable from a phone when practical.

Mobile rules:

- default to stacked card layouts
- keep primary actions reachable
- avoid huge tables
- avoid horizontal overflow
- keep forms short
- support quick capture
- make status readable at a glance

Desktop can expand into command-center grids.

Mobile should feel like a field device.

## View Models

Web apps should use view models or presentation helpers when useful.

Purpose:

- avoid duplicating choice lists in templates
- format dates/times
- prepare compact previews
- limit list counts on Boards
- compute display labels
- keep Web route code readable
- avoid pushing presentation logic into Core

Example local files:

```text
Web/<Domain>/<App>/view_models.py
Web/<Domain>/<App>/ui_choices.py
```

Do not prematurely extract a shared framework until two or more apps prove the pattern.

## Command Surface Pattern

A Web route that mutates state should normally:

1. validate/collect form input
2. call a Skill or approved Core service
3. load updated board/page state
4. render affected partials
5. include feedback or error message
6. log or surface failure clearly

Avoid mutating random files directly in Web route code, swallowing errors silently, returning partials that do not match their targets, or updating only one panel when several visible panels depend on the same state.

## Error UX

Errors should be visible and actionable.

Good error:

> Could not start quest: quest not found. Refresh the page and try again.

Bad error:

> 500

For local/dev apps, traceback logs are fine in the terminal, but user-facing panels should still show a readable message.

## Empty States

Every important panel needs an empty state.

Examples:

- no active quest
- no inbox items
- no habits
- no upcoming events
- no expedition
- no rewards yet
- no Roh suggestions yet

Good empty states should suggest the next action.

Example:

> No active quest. Pick one from Inbox or create a new Quest.

## Confirmation and Reward Feedback

State-changing actions should provide feedback.

Examples:

- “Saved settings.”
- “Habit checked. +5 XP.”
- “Quest started. Expedition deployed.”
- “Quest completed. +90 XP, +10 Tokens.”
- “Inbox item archived.”
- “Roh sorted 4 items.”

For LifeRPG-style apps, reward feedback should be more visible than standard admin feedback.

## App Settings vs Core Settings

Some settings are app-centric. They may still live in NodeCTX Config, but they should be clearly scoped.

Example:

```text
State/main/Global/LifeRPG/Config/settings.json
State/main/Global/LifeRPG/Config/profile.json
```

App settings should not be hidden in Web-only memory.

## React/Vue/Svelte

NSPL does not use React/Vue/Svelte by default.

Current default stack:

- FastAPI
- Jinja
- HTMX
- plain JavaScript
- CSS

A frontend framework may be approved later for a specific app if the need is clear, build tooling is acceptable, state boundaries remain explicit, NodeCTX/Core/Skills are not bypassed, and the app remains portable enough for NSPL goals.

Do not add a frontend framework casually.

## Minimum Web App Quality Bar

A new NSPL Web app should have:

- `web.json`
- `create_app(context)`
- README
- basic tests
- clear launch command
- clean default page
- meaningful empty states
- no raw CRUD wall as homepage
- mobile-safe layout
- durable state through approved seams
- stable HTMX targets if using HTMX
- manual smoke instructions

## LifeRPG-Specific Lessons

LifeRPG should remain the reference case for this contract.

The first management pass failed because it exposed every edit form inline, made the Board a CRUD wall, used enum text boxes, showed fake settings, and tested panel existence more than user experience.

The rescue pass improved it by restoring a compact Board, adding view models and choice helpers, using progressive disclosure, converting enums to selects, making settings affect visible behavior, and using OOB updates where practical.

Future apps should start from the rescued pattern, not repeat the failed one.

## Summary

The NSPL Web UX rule in one sentence:

> Make Web apps feel like purposeful command surfaces over durable state, not accidental admin panels over files.
