# Fusion 360 MCP Server

Control Autodesk Fusion 360 with Claude AI through the Model Context Protocol (MCP).

![MCP Version](https://img.shields.io/badge/MCP-1.0-blue)
![Fusion 360](https://img.shields.io/badge/Fusion%20360-2024+-orange)
![Python](https://img.shields.io/badge/Python-3.10+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## What This Does

This MCP server lets Claude AI directly control Fusion 360 to:
- Create 3D sketches, extrusions, revolves, and sweeps
- Build multi-component assemblies with proper positioning
- Apply fillets, chamfers, shells, and patterns
- Export to STL, STEP, and 3MF formats
- Measure geometry and verify designs

**Example prompt:** *"Create a 50mm cube with 5mm rounded edges"* Ã¢â€ â€™ Claude creates it directly in Fusion 360.

---

## Quick Start (5 minutes)

### Prerequisites
- Autodesk Fusion 360 (free for personal use)
- Claude Desktop app with MCP support
- Python 3.10+ with `pip`

### Step 1: Install the MCP Server

```bash
# Install the MCP framework
pip install mcp

# Clone this repository (or download ZIP)
git clone https://github.com/YOUR_USERNAME/fusion360-mcp.git
cd fusion360-mcp
```

### Step 2: Install the Fusion 360 Add-in

1. Open Fusion 360
2. Go to **Utilities** Ã¢â€ â€™ **ADD-INS** (or press `Shift+S`)
3. Click **Add-Ins** tab Ã¢â€ â€™ **Green Plus (+)** button
4. Navigate to the `fusion-addin` folder from this repo
5. Select `FusionMCP` folder Ã¢â€ â€™ Click **Open**
6. Check **Run on Startup** Ã¢â€ â€™ Click **Run**

You should see: *"Fusion MCP Started! Listening at: C:\Users\...\fusion_mcp_comm"*

### Step 3: Configure Claude Desktop

Edit your Claude Desktop config file:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`  
**Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`

Add this to the `mcpServers` section:

```json
{
  "mcpServers": {
    "fusion360": {
      "command": "python",
      "args": ["C:/path/to/fusion360-mcp/mcp-server/fusion360_mcp_server.py"]
    }
  }
}
```

Ã¢Å¡Â Ã¯Â¸Â **Use forward slashes** in the path, even on Windows.

### Step 4: Add the Skill File (Recommended)

For best results, create a **Claude Project** and paste the contents of `docs/SKILL.md` into the **Project Instructions**. This teaches Claude:
- Fusion 360 coordinate system rules
- Unit conventions (everything in centimeters!)
- Best practices for assemblies
- Common pitfalls to avoid

**For advanced spatial reasoning**, also include `docs/SPATIAL_AWARENESS.md`. This teaches Claude:
- How to verify geometry placement BEFORE operations
- Coordinate mapping between sketch planes and world space
- The critical Z-negation rule for XZ/YZ planes
- Pre/post operation verification protocols

### Step 5: Restart and Test

1. Restart Claude Desktop
2. Open Fusion 360 (ensure the add-in is running)
3. Ask Claude: *"Create a simple box that is 5cm x 3cm x 2cm"*

---

## How It Works

```
Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â     MCP      Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â    File     Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â
Ã¢â€â€š   Claude    Ã¢â€â€š Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬ Ã¢â€â€š  MCP Server         Ã¢â€â€š Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬ Ã¢â€â€š  Fusion 360 Ã¢â€â€š
Ã¢â€â€š   Desktop   Ã¢â€â€š   Protocol   Ã¢â€â€š  (fusion360_mcp_    Ã¢â€â€š   System    Ã¢â€â€š  Add-in     Ã¢â€â€š
Ã¢â€â€š             Ã¢â€â€š              Ã¢â€â€š   server.py)        Ã¢â€â€š             Ã¢â€â€š  (FusionMCP)Ã¢â€â€š
Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ              Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ             Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ
```

1. Claude sends commands via MCP protocol
2. MCP server writes command to `~/fusion_mcp_comm/command_*.json`
3. Fusion add-in polls for commands, executes them via Fusion API
4. Results written to `~/fusion_mcp_comm/response_*.json`
5. MCP server returns result to Claude

---

## Available Tools

| Category | Tools |
|----------|-------|
| **Sketching** | `create_sketch`, `draw_rectangle`, `draw_circle`, `draw_line`, `draw_arc`, `draw_polygon`, `draw_slot`, `finish_sketch` |
| **3D Operations** | `extrude`, `revolve`, `sweep`, `loft`, `shell`, `draft` |
| **Modifications** | `fillet`, `chamfer`, `combine`, `split_body` |
| **Patterns** | `pattern_rectangular`, `pattern_circular`, `mirror` |
| **Components** | `create_component`, `move_component`, `rotate_component`, `list_components` |
| **Export/Import** | `export_stl`, `export_step`, `export_3mf`, `import_mesh` |
| **Inspection** | `get_design_info`, `get_body_info`, `measure`, `fit_view` |
| **Batch** | `batch_operations` (5-10x faster for multiple operations) |

See `docs/TOOL_REFERENCE.md` for complete API documentation.

---

## Important: Units Are in Centimeters!

Ã¢Å¡Â Ã¯Â¸Â **All dimensions in the MCP are in CENTIMETERS**, not millimeters.

| You Want | You Enter |
|----------|-----------|
| 50 mm | `5.0` |
| 100 mm | `10.0` |
| 1 inch | `2.54` |

This is the most common source of errors. A value of `50` means 50 cm (half a meter)!

---

## Project Structure

```
fusion360-mcp/
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ README.md                 # This file
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ LICENSE                   # MIT License
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ mcp-server/
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ fusion360_mcp_server.py   # MCP server (run by Claude Desktop)
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ fusion-addin/
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ FusionMCP.py          # Fusion 360 add-in code
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ FusionMCP.manifest    # Add-in manifest
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ docs/
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ SKILL.md              # Claude Project instructions
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ SPATIAL_AWARENESS.md  # 3D coordinate system & verification
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ TOOL_REFERENCE.md     # Complete API reference
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ KNOWN_ISSUES.md       # Common pitfalls and solutions
Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ examples/
    Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ getting_started.md    # Tutorial examples
```

---

## Troubleshooting

### "Timeout after 45s" Error
- Fusion 360 is not running, OR
- The FusionMCP add-in is not started
- **Fix:** Open Fusion 360 Ã¢â€ â€™ Utilities Ã¢â€ â€™ Add-Ins Ã¢â€ â€™ Run FusionMCP

### Claude doesn't see the Fusion 360 tools
- MCP server path is wrong in config
- Python can't find the `mcp` package
- **Fix:** Verify path uses forward slashes, run `pip install mcp`

### Dimensions are way too big/small
- You're using millimeters instead of centimeters
- **Fix:** Divide all mm values by 10

### Add-in won't install
- Folder structure is wrong
- **Fix:** The add-in folder must contain both `.py` and `.manifest` files

---

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## License

MIT License - see LICENSE file.

---

## Credits

- MCP Server & Add-in developed with Claude AI (Anthropic)
- Uses the [Model Context Protocol](https://modelcontextprotocol.io/) by Anthropic
- Built for [Autodesk Fusion 360](https://www.autodesk.com/products/fusion-360/)
