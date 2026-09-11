# Alexa+ MCP Add-on Onboarding

## Current verified MCP endpoint

- MCP server: `https://caios-care-agent-strands.onrender.com/mcp`
- Transport: Streamable HTTP
- MCP protocol: `2025-11-25`
- Runtime tool discovery: 6 tools
- Service auth: OAuth client credentials (`mcp:service`) enabled
- Safety runtime checks: owner approval receipt/replay guard and red-flag professional escalation verified on Render

## Alexa AI CLI setup

Install the current Alexa AI CLI and authenticate with the Alexa developer account:

```bash
npm install -g @alexa-ai/cli
alexa-ai --version
alexa-ai configure
```

`alexa-ai configure` opens Login with Amazon and stores developer credentials locally. This login step must be completed by the account owner.

## Scaffold the MCP add-on

```bash
alexa-ai new mcp \
  --name "CAIOS Care Agent" \
  --locale en-US \
  --mcp-server-url "https://caios-care-agent-strands.onrender.com/mcp"
```

Review the generated `addon-package/addon.json` before deployment. Do not invent schema fields by hand if the CLI-generated schema differs from documentation.

Suggested copy:

- Short description: `A governed companion-animal care agent for safe follow-up, context capture, and professional escalation.`
- Example phrase 1: `Ask CAIOS what I should follow up on for my pet.`
- Example phrase 2: `Ask CAIOS to record a home observation for my pet.`
- Example phrase 3: `Ask CAIOS whether this follow-up needs my approval.`
- Example phrase 4: `Ask CAIOS what to do when my pet shows a red-flag symptom.`

## Required before deploy

Provide public HTTPS URLs for:

- Privacy policy
- Terms of use
- Required media assets/icons

Do not submit placeholder URLs.

## Deploy and test

```bash
alexa-ai deploy
alexa-ai test
```

After deployment, use the Alexa+ web simulator to capture end-to-end evidence of:

1. Alexa+ discovering the CAIOS MCP tools.
2. A non-urgent follow-up that requires explicit owner approval.
3. A one-time authorization receipt being consumed for the outcome.
4. Replay of the same receipt being rejected.
5. A red-flag observation (`collapse` + `difficulty_breathing`) forcing `PROFESSIONAL_ESCALATION` even when owner approval is true.

## Evidence rule

Do not mark `ALEXA+ INVOCATION` as PASS until an actual Alexa+ development-stage invocation is observed in the simulator or device and the corresponding MCP request appears in server logs.
