# Fusion 360 CAD Skill Library

Spatial reasoning, engineering literacy, and manufacturing awareness for AI-assisted CAD modeling in Autodesk Fusion 360.

## What This Is

A collection of skill files that teach Claude (or any LLM) how to reason about 3D geometry, coordinate systems, manufacturing constraints, and engineering design when operating Fusion 360 through AuraFriday MCP-Link.

This is **not** an MCP server. The original rahayesj MCP server code is preserved in `archive/` for reference. Actual Fusion 360 execution is handled by [AuraFriday MCP-Link](https://apps.autodesk.com/FUSION/en/Detail/Index?id=7269770001970905100), which provides full Fusion 360 API access.

## Skill Files

| File | Purpose | Load When |
|------|---------|-----------|
| `skills/SKILL.md` | Coordinate systems, assembly positioning, manufacturing guidelines, verified lessons learned | Always |
| `skills/SPATIAL_AWARENESS.md` | Pre/post operation verification, error case library, bounding box interpretation | Always |
| `skills/ENGINEERING_LITERACY.md` | Model-vs-reality protocol, manufacturing method declaration, tolerances, assembly hierarchy | Always |
| `skills/AURAFRIDAY_PATTERNS.md` | Python execution templates, common API recipes for AuraFriday | Always |
| `skills/KNOWN_ISSUES.md` | Troubleshooting reference for common Fusion 360 pitfalls | As needed |
| `skills/BUILD123D_BRIDGE.md` | Concept mapping for teams migrating from Build123d | As needed |

## Quick Start

### Prerequisites
- Autodesk Fusion 360 (free for personal use)
- AuraFriday MCP-Link ([server](https://github.com/AuraFriday/mcp-link-server/releases/tag/latest) + [Fusion add-in](https://apps.autodesk.com/FUSION/en/Detail/Index?id=7269770001970905100))
- Claude Desktop or Claude Code

### Setup
1. Install Fusion 360, AuraFriday MCP-Link server, and the Fusion add-in
2. Configure Claude's MCP settings to connect to AuraFriday (see `integration/AURAFRIDAY_SETUP.md`)
3. Load skill files into your Claude project or CLAUDE.md

### For Claude Desktop
Create a project and add the skill files from `skills/` as project knowledge.

### For Claude Code
Reference the skill files in your project's CLAUDE.md:
```markdown
## Fusion 360 CAD Skills
When performing CAD operations, load and follow these skill files:
- C:\path\to\ClaudeFusion360MCP\skills\SKILL.md
- C:\path\to\ClaudeFusion360MCP\skills\SPATIAL_AWARENESS.md
- C:\path\to\ClaudeFusion360MCP\skills\ENGINEERING_LITERACY.md
- C:\path\to\ClaudeFusion360MCP\skills\AURAFRIDAY_PATTERNS.md
```

## Critical Rules (Summary)

1. **ALL dimensions in centimeters** -- Fusion API internal unit is cm. 50mm = 5.0, not 50.
2. **Z-negation on XZ/YZ planes** -- sketch coordinates negate World Z. Empirically verified.
3. **Face/edge indices are unstable** -- re-query after every geometry operation.
4. **Never auto-join** -- create bodies separately, verify with user, then combine.
5. **Export != Save** -- separate operations.

## Repository Structure

```
ClaudeFusion360MCP/
+-- skills/          # Skill files for CAD agents
+-- integration/     # AuraFriday setup and verification
+-- archive/         # Original rahayesj MCP code (preserved)
+-- docs/            # Analysis and research
```

## Origin

Forked from [rahayesj/ClaudeFusion360MCP](https://github.com/rahayesj/ClaudeFusion360MCP), which pioneered the Claude-to-Fusion-360 concept with a 35-tool MCP server. This fork retains the exceptional spatial reasoning documentation and adds engineering literacy, while pivoting execution to AuraFriday MCP-Link for complete Fusion 360 API access.

## Links

- [AuraFriday MCP-Link (App Store)](https://apps.autodesk.com/FUSION/en/Detail/Index?id=7269770001970905100)
- [AuraFriday MCP-Link Server (Releases)](https://github.com/AuraFriday/mcp-link-server/releases/tag/latest)
- [Original rahayesj Repository](https://github.com/rahayesj/ClaudeFusion360MCP)

## License

MIT License - see LICENSE file.
