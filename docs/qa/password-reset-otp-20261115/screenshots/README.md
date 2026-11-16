# Password recovery by email code — screenshots

Captured from the local demo (`npm start`, http://localhost:18080, mail in
Mailpit) by `node scripts/capture_password_otp.mjs`. Light theme, 1280×800 CSS
pixels; the mobile capture is 390×844. Each language performs a real reset for
`learner@dbcas.local`, so the script ends with the demo password `Demo12345!`.
`manifest.json` lists every file written.

| Step | Tiếng Việt | English |
| --- | --- | --- |
| 1. Sign-in page with "Forgot password?" | [vi](vi-01-login.png) | [en](en-01-login.png) |
| 2. Enter the account email | [vi](vi-02-request-code.png) | [en](en-02-request-code.png) |
| 3. Enter the 6-digit code | [vi](vi-03-enter-code.png) | [en](en-03-enter-code.png) |
| 4. Wrong code (field cleared, retry allowed) | [vi](vi-04-wrong-code.png) | [en](en-04-wrong-code.png) |
| 5. Choose a new password (no token in the URL) | [vi](vi-05-new-password.png) | [en](en-05-new-password.png) |
| 6. Password updated | [vi](vi-06-success.png) | [en](en-06-success.png) |
| 7. Fifth wrong code: code invalidated, back to sign-in | [vi](vi-07-too-many-attempts.png) | [en](en-07-too-many-attempts.png) |

- [Verification email in Mailpit](email-code.png) (bilingual plain text, code only, no link).
- [Code page at 390 px](en-mobile-390-enter-code.png).
