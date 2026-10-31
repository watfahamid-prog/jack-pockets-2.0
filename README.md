# Jack Pockets 2.0

An AI-assisted, cloud-executed system for making original, footage-led long-form documentaries and explainers.

## The simple architecture

1. **ChatGPT — editorial brain:** research, source checking, storytelling, scripts, visual planning and editorial review.
2. **GitHub — project headquarters:** code, approved scripts, production briefs, configuration and version history.
3. **GitHub Actions — production computer:** runs the workflow in GitHub's cloud for media processing, editing, rendering and automated quality checks.
4. **Deliverables — finished work:** MP4, captions, source/rights notes and a short QC report.

Your laptop is not part of production. It can be switched off while Actions runs.

## How ChatGPT and GitHub work together

ChatGPT prepares or revises project files and can save them directly into this repository through the connected GitHub integration. This avoids copying long scripts and plans between ChatGPT and GitHub by hand.

Actions reads the committed files. It cannot read the private contents of a ChatGPT conversation unless those contents are deliberately saved to the repository or passed as workflow inputs.

## Keep the first version small

Start with one simple production path. Do not add a database, agent framework, complex adapter system or background service until a working video demonstrates the need.

## Cost rule

- Target operating cost: **0 SEK**.
- Do not add paid API calls, subscriptions, credits, larger runners or paid storage without explicit approval.
- If a provider's price, quota or overage behavior is unknown, stop instead of trying another provider.
- Do not place API keys, passwords, personal data or private source material in this public repository.
- Automatic model API calls are not enabled yet. ChatGPT can prepare and commit the script/brief directly; a workflow-based model provider may be added only after its terms, eligibility, free quota and hard-stop behavior are verified.

## Storage rule

- **Actions artifacts:** temporary test outputs and review files only. The current smoke-test artifact expires after 3 days.
- **GitHub Releases:** intended destination for final, approved, public MP4 deliverables. A release is public because this repository is public. Never create a public release before the final video is explicitly approved.
- **Working footage and private drafts:** do not commit them to this public repository. A separate private storage option is not configured.

GitHub documents a 2 GiB per-file limit for release assets; check the file size before using this destination.

## Current state

- [Cloud render smoke test](.github/workflows/cloud-render-smoke-test.yml) is in place.
- Run 1 succeeded: 12-second H.264/AAC MP4, 1280x720, 30 FPS, with FFprobe validation.
- This proves cloud rendering and artifact upload. It does **not** prove documentary quality or the full AI production pipeline.

## Next milestone

Create one short, real documentary segment using an approved ChatGPT-written brief/script, cleared footage, narration, captions, music and a simple edit. Inspect the actual MP4 before expanding the system.
