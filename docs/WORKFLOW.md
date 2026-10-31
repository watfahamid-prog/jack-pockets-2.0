# How the project works

Keep this intentionally simple.

## Make a video

1. Discuss the topic and research with ChatGPT.
2. ChatGPT prepares the approved script and production brief, then saves them directly in the repository. No manual copy/paste is needed when the GitHub connection can update the files.
3. Start the appropriate workflow from the repository's **Actions** page.
4. GitHub Actions runs on a GitHub-hosted cloud runner. Your laptop can be off.
5. Inspect the MP4, source/rights notes and QC report.
6. Only after explicit approval, publish the final video as a GitHub Release asset.

## What is automated today?

The cloud-render smoke test renders a synthetic test pattern and tone. It verifies that FFmpeg can create and validate an MP4 on a hosted runner and upload it as an Actions artifact.

It is a technical test, not a documentary generator.

## AI handoff

ChatGPT is currently the script/research model. Approved content is saved into GitHub files directly through the connected GitHub integration.

The Actions workflow does not yet call an AI API. That is deliberately not blocked forever: an automated model call can be added when a provider is confirmed to be available to the account, allowed by its terms, genuinely free within a defined quota, and unable to create charges. Never assume a ChatGPT subscription includes API usage.

## Storage

- Use Actions artifacts for short-lived test/review outputs.
- Use public GitHub Releases for final videos only after approval.
- Do not store drafts, keys or private material in this public repository.
- If a future project needs private media storage, choose and verify a separate free service before adding it.

## Development rule

One working end-to-end video first. Add only the next piece that is needed. Passing code tests is not the same as accepting the finished video.
