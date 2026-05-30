# Web App UX Patterns

NSPL Web apps are command surfaces, not admin consoles. See `Docs/Agents/06_NSPL_WEB_APP_UX_CONTRACT.md` for the full contract.

## Progressive Disclosure

Default views should use compact cards or rows. Show full forms only when requested.

```html
<article class="item-card">
  <strong>{{ quest.title }}</strong>
  <div class="actions">
    <button>Start</button>
    <details>
      <summary>Edit</summary>
      <form hx-post="/quest/edit" hx-target="#quest-panel" hx-swap="outerHTML">
        ...
      </form>
    </details>
  </div>
</article>
```

Avoid always-visible edit forms for every existing item.

## Enum Fields

Use constrained controls for known values.

```html
<select name="status">
  <option value="open">open</option>
  <option value="active">active</option>
  <option value="paused">paused</option>
  <option value="completed">completed</option>
  <option value="archived">archived</option>
</select>
```

Do not use free-text fields for categories, status, cadence, strictness, visual mode, or similar enum-style fields.

## HTMX Panels

Return whole panels with stable IDs and replace them with `outerHTML`.

```html
<section id="inbox-panel">
  ...
</section>

<form hx-post="/quick-dump" hx-target="#inbox-panel" hx-swap="outerHTML">
  ...
</form>
```

Avoid returning a full panel into `innerHTML` or targeting `closest section` for full-panel replacements.

## Out-Of-Band Swaps

When one action affects multiple panels, include OOB updates.

```html
<section id="active-session-panel">...</section>
<section id="expedition-panel" hx-swap-oob="outerHTML">...</section>
<section id="reward-panel" hx-swap-oob="outerHTML">...</section>
```

Use this for starts, completes, sorting, settings changes, and any action where visible state would otherwise feel stale.

## Tests

UX tests should assert behavior users can see:

- dashboards do not show CRUD walls
- edit forms are collapsed by default
- select fields render for enums
- state-changing actions update related panels
- unsafe HTMX nesting patterns are absent

Route-200 tests are not enough.
