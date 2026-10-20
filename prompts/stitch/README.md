# Stitch order (6 generations, free tier is ~350/month)
1. S1 first. Then export/save the design system as DESIGN.md in the repo root (Stitch `design-md` skill via MCP, or copy it by hand).
2. S2..S6, one screen each. Export HTML/CSS to design/ as library.html, watch.html, interview-setup.html, interview-live.html, scorecard.html.
3. Optional MCP: in Antigravity open the agent menu > MCP Servers > install `stitch`, paste the Stitch API key (Stitch Settings > Create API Key). Not needed if you save HTML files by hand.
Files owned by this step: DESIGN.md, design/README.md (+ exported design/*.html). Stitch exports HTML/CSS only (React export not available as of the sources checked), so M4 converts HTML to React.
