# Getting Started with Fusion 360 MCP

Simple examples to test your installation.

---

## Example 1: Simple Box

**Prompt to Claude:**
> Create a box that is 5cm wide, 3cm deep, and 2cm tall.

**What Claude should do:**
```
1. create_sketch(plane="XY", offset=0)
2. draw_rectangle(x=-2.5, y=-1.5, width=5, height=3)
3. finish_sketch()
4. extrude(distance=2, direction="positive")
```

**Result:** A 50mm × 30mm × 20mm box centered on the origin.

---

## Example 2: Rounded Box

**Prompt to Claude:**
> Create a 4cm cube with 3mm rounded edges.

**What Claude should do:**
```
1. create_sketch(plane="XY", offset=0)
2. draw_rectangle(x=-2, y=-2, width=4, height=4)
3. finish_sketch()
4. extrude(distance=4, direction="positive")
5. fillet(radius=0.3, edges="all")
```

**Result:** A 40mm cube with all edges rounded to 3mm radius.

---

## Example 3: Cylinder with Hole

**Prompt to Claude:**
> Make a cylinder 3cm diameter, 5cm tall, with a 1cm hole through the center.

**What Claude should do:**
```
1. create_sketch(plane="XY", offset=0)
2. draw_circle(x=0, y=0, radius=1.5)      # Outer diameter
3. draw_circle(x=0, y=0, radius=0.5)      # Inner hole
4. finish_sketch()
5. extrude(distance=5, direction="positive", profile_index=0)  # Outer ring only
```

**Result:** A hollow cylinder (tube) 30mm OD, 10mm ID, 50mm tall.

---

## Example 4: Two-Part Assembly

**Prompt to Claude:**
> Create a base plate 10cm × 10cm × 0.5cm, then put a 2cm cube on top of it.

**What Claude should do:**
```
# Part 1: Base plate
1. create_component(name="Base_Plate")
2. create_sketch(plane="XY", offset=0)
3. draw_rectangle(x=-5, y=-5, width=10, height=10)
4. finish_sketch()
5. extrude(distance=0.5, direction="positive")

# Part 2: Cube on top
6. create_component(name="Top_Cube")
7. create_sketch(plane="XY", offset=0.5)   # Start at top of base
8. draw_rectangle(x=-1, y=-1, width=2, height=2)
9. finish_sketch()
10. extrude(distance=2, direction="positive")
```

**Result:** A 100mm square base with a 20mm cube sitting on top.

---

## Example 5: Export for 3D Printing

**Prompt to Claude:**
> Export the current design as an STL file for 3D printing.

**What Claude should do:**
```
1. export_stl(filepath="C:/Users/YourName/Desktop/my_part.stl")
```

**Note:** User must provide a valid path. Claude should ask if not specified.

---

## Common Mistakes

### ❌ Wrong (using millimeters)
```
draw_rectangle(x=-25, y=-15, width=50, height=30)  # Creates 50cm box!
```

### ✅ Correct (using centimeters)
```
draw_rectangle(x=-2.5, y=-1.5, width=5, height=3)  # Creates 5cm box
```

---

## Testing the Connection

If Claude can't connect, try this diagnostic prompt:

> Get the current design info from Fusion 360.

Claude should call `get_design_info()` and return something like:
```json
{
  "success": true,
  "design_name": "Untitled",
  "components": 1,
  "bodies": 0,
  "sketches": 0
}
```

If this fails with "Timeout", the add-in isn't running in Fusion 360.