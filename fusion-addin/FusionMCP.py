import adsk.core
import adsk.fusion
import traceback
import json
import time
import threading
from pathlib import Path

app = None
ui = None
stop_thread = False
monitor_thread = None

COMM_DIR = Path.home() / "fusion_mcp_comm"

def run(context):
    global app, ui, monitor_thread, stop_thread
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        COMM_DIR.mkdir(exist_ok=True)
        stop_thread = False
        monitor_thread = threading.Thread(target=monitor_commands, daemon=True)
        monitor_thread.start()
        ui.messageBox('Fusion MCP Started!\n\nListening at:\n' + str(COMM_DIR))
    except:
        if ui:
            ui.messageBox('Failed:\n' + traceback.format_exc())

def stop(context):
    global stop_thread, ui
    try:
        stop_thread = True
        if ui:
            ui.messageBox('Fusion MCP Stopped')
    except:
        pass

def monitor_commands():
    global stop_thread
    while not stop_thread:
        try:
            cmd_files = list(COMM_DIR.glob("command_*.json"))
            for cmd_file in cmd_files:
                try:
                    with open(cmd_file, 'r') as f:
                        command = json.load(f)
                    result = execute_command(command)
                    resp_file = COMM_DIR / f"response_{command['id']}.json"
                    with open(resp_file, 'w') as f:
                        json.dump(result, f, indent=2)
                except Exception as e:
                    pass
            time.sleep(0.1)
        except:
            pass

def execute_command(command):
    global app
    tool_name = command.get('name')
    params = command.get('params', {})
    try:
        design = app.activeProduct
        if not design:
            return {"success": False, "error": "No active design"}
        rootComp = design.rootComponent
        
        if tool_name == 'create_sketch':
            return create_sketch(design, rootComp, params)
        elif tool_name == 'draw_circle':
            return draw_circle(design, rootComp, params)
        elif tool_name == 'draw_rectangle':
            return draw_rectangle(design, rootComp, params)
        elif tool_name == 'extrude':
            return extrude_profile(design, rootComp, params)
        elif tool_name == 'revolve':
            return revolve_profile(design, rootComp, params)
        elif tool_name == 'fillet':
            return add_fillet(design, rootComp, params)
        elif tool_name == 'finish_sketch':
            return finish_sketch(design, rootComp, params)
        elif tool_name == 'fit_view':
            return fit_view(design, rootComp, params)
        elif tool_name == 'get_design_info':
            return get_design_info(design, rootComp, params)
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_sketch(design, rootComp, params):
    plane_name = params.get('plane', 'XY')
    plane_map = {
        'XY': rootComp.xYConstructionPlane,
        'XZ': rootComp.xZConstructionPlane,
        'YZ': rootComp.yZConstructionPlane
    }
    plane = plane_map.get(plane_name)
    sketch = rootComp.sketches.add(plane)
    return {"success": True, "sketch_name": sketch.name}

def draw_circle(design, rootComp, params):
    activeEdit = design.activeEditObject
    if not activeEdit:
        return {"success": False, "error": "No active sketch"}
    sketch = activeEdit
    center = adsk.core.Point3D.create(params['center_x'], params['center_y'], 0)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(center, params['radius'])
    return {"success": True}

def draw_rectangle(design, rootComp, params):
    activeEdit = design.activeEditObject
    if not activeEdit:
        return {"success": False, "error": "No active sketch"}
    sketch = activeEdit
    p1 = adsk.core.Point3D.create(params['x1'], params['y1'], 0)
    p2 = adsk.core.Point3D.create(params['x2'], params['y2'], 0)
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(p1, p2)
    return {"success": True}

def extrude_profile(design, rootComp, params):
    if rootComp.sketches.count == 0:
        return {"success": False, "error": "No sketches"}
    sketch = rootComp.sketches.item(rootComp.sketches.count - 1)
    if sketch.profiles.count == 0:
        return {"success": False, "error": "No profiles"}
    profile = sketch.profiles.item(sketch.profiles.count - 1)
    extrudes = rootComp.features.extrudeFeatures
    extInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(params['distance']))
    extrude = extrudes.add(extInput)
    return {"success": True, "feature_name": extrude.name}

def revolve_profile(design, rootComp, params):
    if rootComp.sketches.count == 0:
        return {"success": False, "error": "No sketches"}
    sketch = rootComp.sketches.item(rootComp.sketches.count - 1)
    if sketch.profiles.count == 0:
        return {"success": False, "error": "No profiles"}
    profile = sketch.profiles.item(sketch.profiles.count - 1)
    axis = rootComp.yConstructionAxis
    revolves = rootComp.features.revolveFeatures
    revInput = revolves.createInput(profile, axis, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    import math
    revInput.setAngleExtent(False, adsk.core.ValueInput.createByReal(math.radians(params['angle'])))
    revolve = revolves.add(revInput)
    return {"success": True, "feature_name": revolve.name}

def add_fillet(design, rootComp, params):
    if rootComp.bRepBodies.count == 0:
        return {"success": False, "error": "No bodies"}
    body = rootComp.bRepBodies.item(rootComp.bRepBodies.count - 1)
    edges = adsk.core.ObjectCollection.create()
    for edge in body.edges:
        edges.add(edge)
    fillets = rootComp.features.filletFeatures
    filletInput = fillets.createInput()
    filletInput.addConstantRadiusEdgeSet(edges, adsk.core.ValueInput.createByReal(params['radius']), True)
    fillet = fillets.add(filletInput)
    return {"success": True, "feature_name": fillet.name}

def finish_sketch(design, rootComp, params):
    design.activeEditObject = None
    return {"success": True, "message": "Sketch finished"}

def fit_view(design, rootComp, params):
    global app
    app.activeViewport.fit()
    return {"success": True}

def get_design_info(design, rootComp, params):
    return {
        "success": True,
        "design_name": design.parentDocument.name,
        "body_count": rootComp.bRepBodies.count,
        "sketch_count": rootComp.sketches.count
    }
