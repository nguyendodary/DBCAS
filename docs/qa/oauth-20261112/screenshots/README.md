# Authentication restoration screenshots

Before captures: pre-existing running demo at http://localhost:18080.
The source baseline is `60f075a`; the existing image has no source revision stamp.
Both provider statuses are false; neither provider is present in the DOM.
Login and register are captured at 1280 and 390 pixels in light and dark themes.
After captures: changed UI at http://127.0.0.1:5175 against the real unconfigured
API on localhost:18000. `node scripts/capture_oauth.mjs` asserts exact CSS
viewport width and writes [verification.json](verification.json).

| Screen | Light 1280 | Light 390 | Dark 1280 | Dark 390 |
| --- | --- | --- | --- | --- |
| Login before | [image](before-login-light-1280.png) | [image](before-login-light-390.png) | [image](before-login-dark-1280.png) | [image](before-login-dark-390.png) |
| Login after | [image](after-login-light-1280.png) | [image](after-login-light-390.png) | [image](after-login-dark-1280.png) | [image](after-login-dark-390.png) |
| Register before | [image](before-register-light-1280.png) | [image](before-register-light-390.png) | [image](before-register-dark-1280.png) | [image](before-register-dark-390.png) |
| Register after | [image](after-register-light-1280.png) | [image](after-register-light-390.png) | [image](after-register-dark-1280.png) | [image](after-register-dark-390.png) |

[Mobile unavailable-provider notice](after-notice-light-390.png).
All 16 states have no horizontal overflow; before has zero provider controls,
after has two. Interactive-profile captures with incorrect zoom were replaced
before review; only exact-dimension images are retained.

[Final rebuilt demo, light/390 with unavailable-provider notice](final-demo-login-light-390.png)
is captured on **localhost:18080** from the final runtime code `afc6e49`.
Both demo logins, 16 screen/theme/language/width states and 32 notices pass
on that image, with no external requests or page errors.
