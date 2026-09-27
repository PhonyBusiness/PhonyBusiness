# PhonyBusiness frontend

Plain HTML, CSS, and JavaScript with no build step and no npm. A resident takes a
simulated scam call in the browser, gets a result with tips, and the dashboard
shows trends across all calls.

## Run it

From the project root:

```sh
python3 -m http.server 5500 --directory frontend
```

- Call flow: http://localhost:5500
- Dashboard: http://localhost:5500/dashboard.html

The backend must be running too (see the root README). After changing a file,
hard-refresh the browser (Cmd+Shift+R) so it doesn't use a cached copy.

## Point it at a backend

The backend URL is set at the top of two files:

```js
// app.js and dashboard.js
const API = "https://clapped-boondocks-basics.ngrok-free.dev";
```

Use `http://localhost:8000` for a local backend, or an ngrok or deployed URL.
Every request sends the `ngrok-skip-browser-warning` header. Without it, ngrok's
free plan returns an HTML warning page instead of JSON.

The microphone only works on `localhost` or over HTTPS. To test on a phone, open
the page through an HTTPS URL, such as an ngrok tunnel to port 5500.

## How it works

`index.html` holds four screens, and `app.js` shows one at a time:

1. **Start:** name, phone number, scenario, and difficulty. The gator gets more
   evil as details are filled in, and the page theme follows the difficulty.
2. **Ringing:** the gator, in disguise, calls the resident. Decline goes back;
   Accept starts the call.
3. **In call:** the browser talks directly to the ElevenLabs agent through the
   ElevenLabs JS SDK, using a signed URL from the backend. The gator's mouth
   moves while the agent speaks, and the resident's mouth moves with your
   microphone.
4. **Recap:** pass, fail, or stopped, with an ending scene, red flags, and tips.

`dashboard.html` shows the scoreboard, insights, trends, what fools people, how
callers felt, and recent calls. Click a recent call to see its frustration and
sentiment over time.

The mascot drawings are inline SVG, defined once in `index.html`. `app.js` copies
them onto the other screens, and `dashboard.js` loads them from `index.html`, so
editing them in one place updates every page.

## Files

| File | What it does |
| --- | --- |
| `index.html` | The call flow's four screens and the mascot SVGs |
| `app.js` | Call-flow logic: API calls, ElevenLabs session, timer, mascots, recap |
| `style.css` | Shared base styles, including buttons, inputs, and the recap |
| `mascots.css` | Mascot moods, animations, and difficulty themes |
| `dashboard.html` / `dashboard.js` / `dashboard.css` | The dashboard (charts use Chart.js from a CDN) |

## Backend endpoints used

| Page | Endpoints |
| --- | --- |
| Call flow | `GET /scenarios`, `POST /calls/start`, `POST /calls/{id}/session`, `POST /calls/{id}/hangup`, `GET /calls/{id}` |
| Dashboard | `GET /analytics/overview`, `/wellbeing`, `/risk`, `/trends?days=N`, `/conversations`, `/conversations/{id}` |

Dashboard data comes from the ElevenLabs post-call webhook, so a finished call
appears a few seconds after it ends. Press **Refresh** to see it.
