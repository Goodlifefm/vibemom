# Mini App Production Verification

## VPS: 3 Commands

1. Watch API logs for client confirmation (must include `CLIENT_LOG` and then real project requests):

```bash
docker compose logs api --tail=200 | grep CLIENT_LOG
```

2. Confirm API is alive and which version it serves:

```bash
curl -s https://api.vibemom.ru/healthz && echo
curl -s https://api.vibemom.ru/version && echo
```

3. Confirm which frontend build is serving the domain (no Vercel UI):

```bash
curl -s https://app.vibemom.ru/build.json && echo
```

## Phone: 5-Tap Acceptance

1. Open the Telegram Mini App on the phone.
2. At the bottom, find the build stamp and tap the `⚙︎` button (Self-test).
3. In Self-test, tap `Log to server`.
4. On screen, confirm you see: `Logged OK (id=...)`.
5. In Self-test, tap `List projects` and then `Open first project` to generate real API traffic.
6. On the VPS, `grep CLIENT_LOG` (and/or the `request_id`) in API logs and confirm:

   A JSON line with `"tag":"CLIENT_LOG"` includes `build_sha`, `origin`, `ua`, `tap`.

   After that, you see requests for `GET /projects/my` and `GET /projects/{id}` (or an error with status).
