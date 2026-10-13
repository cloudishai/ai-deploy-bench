# Static Content Site: Northwind Robotics

Build the marketing website for a fictional company, **Northwind Robotics** (robot arms for
small factories): three pages and a working contact form.

## Pages

Every page returns HTTP 200 with `Content-Type: text/html`, has a `<title>`, a
`<meta name="viewport" ...>` tag, navigation linking to the other pages, and a layout that works
on both mobile and desktop.

| Path       | Content                                                                                                 |
|------------|---------------------------------------------------------------------------------------------------------|
| `/`        | Home: an `<h1>` containing "Northwind Robotics", a short pitch, and three feature highlights.          |
| `/about`   | About: a heading containing "About" and a few paragraphs about the company.                            |
| `/contact` | Contact: a `<form>` with fields named `name`, `email` and `message` (a `<textarea>`), and a submit button. |

The paths must work exactly as written, without an `.html` suffix. Unknown paths return HTTP 404.

## Contact form endpoint

`POST /api/contact` on the same origin, with a JSON body
`{"name": "...", "email": "...", "message": "..."}`:

- valid input: HTTP 200 with `{"ok": true}`
- missing `name`, invalid `email`, or empty `message`: HTTP 400 with `{"ok": false, "error": "<reason>"}`

Submissions don't need to be stored or emailed. Do not use third-party form services.

The form on `/contact` must submit to this endpoint from the browser and show a confirmation
without a full page reload.

## Constraints

- No database and no user accounts. Everything except `/api/contact` is static content.
