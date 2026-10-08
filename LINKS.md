# Submission Links

- **Name:** Anubhav Jaiswal
- **Reg No:** 2341010007
- **University:** ITER, SOA

## Links

- **GitHub:** https://github.com/anubhav-auth/oraczen-agent-run-explorer
- **Frontend (Vercel):** https://oraczen-agent-run-explorer.vercel.app/runs
- **Dashboard:** https://oraczen-agent-run-explorer.vercel.app/dashboard
- **Backend (Render):** https://oraczen-agent-run-explorer.onrender.com/api/stats
- **Backend docs:** https://oraczen-agent-run-explorer.onrender.com/docs

## Test from scratch (reviewer path)

Needs only Python and Node:

```bash
git clone git@github.com:anubhav-auth/oraczen-agent-run-explorer.git
cd oraczen-agent-run-explorer
make install
make dev
```

Open the links `make dev` prints (http://localhost:3000/runs). For fast page switches use `make prod` instead. Tests: `make test`.
