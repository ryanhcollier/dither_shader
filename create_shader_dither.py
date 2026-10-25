"""
Blender Real-Time Viewport Shader Dither Setup
----------------------------------------------
Author: Antigravity
Compatible with Blender 4.x and Blender 5.x (EEVEE & Material Preview)

Creates a real-time, 100% viewport-native dithering effect inside the Material Shader Editor.
Eliminates the need for post-processing compositor passes!

Features:
- Live 60+ FPS interactive feedback directly in the 3D Viewport
- Shader to RGB pipeline capturing all scene lights, shadows, and BSDF surfaces
- Dual Coordinate Modes:
    * Screen-Space Mode (1.0): Fixed 2D CRT/LCD raster lattice across viewport/camera
    * Object/UV-Space Mode (0.0): 3D surface-anchored dither that sticks to mesh curvature
- Procedural Bayer 4x4 (Classic punchy) & Bayer 8x8 (Smooth 64-level) matrices
- 3 Color Modes:
    * Mode 0: 1-Bit Dual-Tone Tint (Macintosh, Game Boy, Amber/Green CRT)
    * Mode 1: Multi-Level Quantized Posterization (Grayscale)
    * Mode 2: Multi-Bit RGB Channel Quantization (EGA 64-color, Genesis 512-color)
- Organized collapsible panels with intuitive look sliders
- Emission shader output for direct, unshaded pixel-perfect display
"""

import bpy


def create_shader_bayer_4x4():
    """Builds an organized procedural 4x4 Bayer matrix shader node group."""
    group_name = "Shader_Bayer_4x4"
    if group_name in bpy.data.node_groups:
        return bpy.data.node_groups[group_name]

    ng = bpy.data.node_groups.new(name=group_name, type="ShaderNodeTree")
    ng.use_fake_user = True

    ng.interface.new_socket(name="X", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket(name="Y", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket(name="Normalized", in_out="OUTPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket(name="Centered", in_out="OUTPUT", socket_type="NodeSocketFloat")

    nodes = ng.nodes
    links = ng.links

    f_x = nodes.new(type="NodeFrame")
    f_x.label = "X Bit Extraction"
    f_x.use_custom_color = True
    f_x.color = (0.15, 0.25, 0.45)

    f_y = nodes.new(type="NodeFrame")
    f_y.label = "Y Bit Extraction"
    f_y.use_custom_color = True
    f_y.color = (0.15, 0.35, 0.35)

    f_b = nodes.new(type="NodeFrame")
    f_b.label = "Bitwise Interleaving"
    f_b.use_custom_color = True
    f_b.color = (0.35, 0.25, 0.15)

    f_o = nodes.new(type="NodeFrame")
    f_o.label = "Normalization"
    f_o.use_custom_color = True
    f_o.color = (0.25, 0.2, 0.35)

    inp = nodes.new(type="NodeGroupInput")
    inp.location = (-800, 0)
    out = nodes.new(type="NodeGroupOutput")
    out.location = (800, 0)

    # X bits
    x0 = nodes.new(type="ShaderNodeMath")
    x0.operation = 'FLOORED_MODULO'
    x0.inputs[1].default_value = 2.0
    x0.location = (-600, 200)
    x0.parent = f_x
    links.new(inp.outputs["X"], x0.inputs[0])

    div_x = nodes.new(type="ShaderNodeMath")
    div_x.operation = 'DIVIDE'
    div_x.inputs[1].default_value = 2.0
    div_x.location = (-600, 50)
    div_x.parent = f_x
    links.new(inp.outputs["X"], div_x.inputs[0])

    flr_x = nodes.new(type="ShaderNodeMath")
    flr_x.operation = 'FLOOR'
    flr_x.location = (-450, 50)
    flr_x.parent = f_x
    links.new(div_x.outputs["Value"], flr_x.inputs[0])

    x1 = nodes.new(type="ShaderNodeMath")
    x1.operation = 'FLOORED_MODULO'
    x1.inputs[1].default_value = 2.0
    x1.location = (-300, 50)
    x1.parent = f_x
    links.new(flr_x.outputs["Value"], x1.inputs[0])

    # Y bits
    y0 = nodes.new(type="ShaderNodeMath")
    y0.operation = 'FLOORED_MODULO'
    y0.inputs[1].default_value = 2.0
    y0.location = (-600, -100)
    y0.parent = f_y
    links.new(inp.outputs["Y"], y0.inputs[0])

    div_y = nodes.new(type="ShaderNodeMath")
    div_y.operation = 'DIVIDE'
    div_y.inputs[1].default_value = 2.0
    div_y.location = (-600, -250)
    div_y.parent = f_y
    links.new(inp.outputs["Y"], div_y.inputs[0])

    flr_y = nodes.new(type="ShaderNodeMath")
    flr_y.operation = 'FLOOR'
    flr_y.location = (-450, -250)
    flr_y.parent = f_y
    links.new(div_y.outputs["Value"], flr_y.inputs[0])

    y1 = nodes.new(type="ShaderNodeMath")
    y1.operation = 'FLOORED_MODULO'
    y1.inputs[1].default_value = 2.0
    y1.location = (-300, -250)
    y1.parent = f_y
    links.new(flr_y.outputs["Value"], y1.inputs[0])

    # Interleaving
    sub0 = nodes.new(type="ShaderNodeMath")
    sub0.operation = 'SUBTRACT'
    sub0.location = (-150, 200)
    sub0.parent = f_b
    links.new(x0.outputs["Value"], sub0.inputs[0])
    links.new(y0.outputs["Value"], sub0.inputs[1])

    abs0 = nodes.new(type="ShaderNodeMath")
    abs0.operation = 'ABSOLUTE'
    abs0.location = (0, 200)
    abs0.parent = f_b
    links.new(sub0.outputs["Value"], abs0.inputs[0])

    sub1 = nodes.new(type="ShaderNodeMath")
    sub1.operation = 'SUBTRACT'
    sub1.location = (-150, 50)
    sub1.parent = f_b
    links.new(x1.outputs["Value"], sub1.inputs[0])
    links.new(y1.outputs["Value"], sub1.inputs[1])

    abs1 = nodes.new(type="ShaderNodeMath")
    abs1.operation = 'ABSOLUTE'
    abs1.location = (0, 50)
    abs1.parent = f_b
    links.new(sub1.outputs["Value"], abs1.inputs[0])

    mul8 = nodes.new(type="ShaderNodeMath")
    mul8.operation = 'MULTIPLY'
    mul8.inputs[1].default_value = 8.0
    mul8.location = (150, 200)
    mul8.parent = f_b
    links.new(abs0.outputs["Value"], mul8.inputs[0])

    mul4 = nodes.new(type="ShaderNodeMath")
    mul4.operation = 'MULTIPLY'
    mul4.inputs[1].default_value = 4.0
    mul4.location = (150, 50)
    mul4.parent = f_b
    links.new(y0.outputs["Value"], mul4.inputs[0])

    mul2 = nodes.new(type="ShaderNodeMath")
    mul2.operation = 'MULTIPLY'
    mul2.inputs[1].default_value = 2.0
    mul2.location = (150, -100)
    mul2.parent = f_b
    links.new(abs1.outputs["Value"], mul2.inputs[0])

    add1 = nodes.new(type="ShaderNodeMath")
    add1.operation = 'ADD'
    add1.location = (300, 150)
    add1.parent = f_b
    links.new(mul8.outputs["Value"], add1.inputs[0])
    links.new(mul4.outputs["Value"], add1.inputs[1])

    add2 = nodes.new(type="ShaderNodeMath")
    add2.operation = 'ADD'
    add2.location = (300, 0)
    add2.parent = f_b
    links.new(add1.outputs["Value"], add2.inputs[0])
    links.new(mul2.outputs["Value"], add2.inputs[1])

    add_v = nodes.new(type="ShaderNodeMath")
    add_v.operation = 'ADD'
    add_v.location = (450, 0)
    add_v.parent = f_b
    links.new(add2.outputs["Value"], add_v.inputs[0])
    links.new(y1.outputs["Value"], add_v.inputs[1])

    add_half = nodes.new(type="ShaderNodeMath")
    add_half.operation = 'ADD'
    add_half.inputs[1].default_value = 0.5
    add_half.location = (600, 100)
    add_half.parent = f_o
    links.new(add_v.outputs["Value"], add_half.inputs[0])

    div16 = nodes.new(type="ShaderNodeMath")
    div16.operation = 'DIVIDE'
    div16.inputs[1].default_value = 16.0
    div16.location = (600, -50)
    div_half_parent = f_o
    links.new(add_half.outputs["Value"], div16.inputs[0])
    links.new(div16.outputs["Value"], out.inputs["Normalized"])

    sub_half = nodes.new(type="ShaderNodeMath")
    sub_half.operation = 'SUBTRACT'
    sub_half.inputs[1].default_value = 0.5
    sub_half.location = (600, -200)
    sub_half.parent = f_o
    links.new(div16.outputs["Value"], sub_half.inputs[0])
    links.new(sub_half.outputs["Value"], out.inputs["Centered"])

    return ng


def create_shader_bayer_8x8():
    """Builds an organized procedural 8x8 Bayer matrix shader node group."""
    group_name = "Shader_Bayer_8x8"
    if group_name in bpy.data.node_groups:
        return bpy.data.node_groups[group_name]

    ng = bpy.data.node_groups.new(name=group_name, type="ShaderNodeTree")
    ng.use_fake_user = True

    ng.interface.new_socket(name="X", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket(name="Y", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket(name="Normalized", in_out="OUTPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket(name="Centered", in_out="OUTPUT", socket_type="NodeSocketFloat")

    nodes = ng.nodes
    links = ng.links

    f_x = nodes.new(type="NodeFrame")
    f_x.label = "X Bit Extraction (3-bit)"
    f_x.use_custom_color = True
    f_x.color = (0.15, 0.25, 0.45)

    f_y = nodes.new(type="NodeFrame")
    f_y.label = "Y Bit Extraction (3-bit)"
    f_y.use_custom_color = True
    f_y.color = (0.15, 0.35, 0.35)

    f_b = nodes.new(type="NodeFrame")
    f_b.label = "Bayer Interleaving"
    f_b.use_custom_color = True
    f_b.color = (0.35, 0.25, 0.15)

    f_o = nodes.new(type="NodeFrame")
    f_o.label = "Normalization"
    f_o.use_custom_color = True
    f_o.color = (0.25, 0.2, 0.35)

    inp = nodes.new(type="NodeGroupInput")
    inp.location = (-1100, 0)
    out = nodes.new(type="NodeGroupOutput")
    out.location = (1300, 0)

    # X bits
    x0 = nodes.new(type="ShaderNodeMath")
    x0.operation = 'FLOORED_MODULO'
    x0.inputs[1].default_value = 2.0
    x0.location = (-850, 400)
    x0.parent = f_x
    links.new(inp.outputs["X"], x0.inputs[0])

    div_x2 = nodes.new(type="ShaderNodeMath")
    div_x2.operation = 'DIVIDE'
    div_x2.inputs[1].default_value = 2.0
    div_x2.location = (-850, 250)
    div_x2.parent = f_x
    links.new(inp.outputs["X"], div_x2.inputs[0])
    flr_x2 = nodes.new(type="ShaderNodeMath")
    flr_x2.operation = 'FLOOR'
    flr_x2.location = (-680, 250)
    flr_x2.parent = f_x
    links.new(div_x2.outputs["Value"], flr_x2.inputs[0])
    x1 = nodes.new(type="ShaderNodeMath")
    x1.operation = 'FLOORED_MODULO'
    x1.inputs[1].default_value = 2.0
    x1.location = (-510, 250)
    x1.parent = f_x
    links.new(flr_x2.outputs["Value"], x1.inputs[0])

    div_x4 = nodes.new(type="ShaderNodeMath")
    div_x4.operation = 'DIVIDE'
    div_x4.inputs[1].default_value = 4.0
    div_x4.location = (-850, 100)
    div_x4.parent = f_x
    links.new(inp.outputs["X"], div_x4.inputs[0])
    flr_x4 = nodes.new(type="ShaderNodeMath")
    flr_x4.operation = 'FLOOR'
    flr_x4.location = (-680, 100)
    flr_x4.parent = f_x
    links.new(div_x4.outputs["Value"], flr_x4.inputs[0])
    x2 = nodes.new(type="ShaderNodeMath")
    x2.operation = 'FLOORED_MODULO'
    x2.inputs[1].default_value = 2.0
    x2.location = (-510, 100)
    x2.parent = f_x
    links.new(flr_x4.outputs["Value"], x2.inputs[0])

    # Y bits
    y0 = nodes.new(type="ShaderNodeMath")
    y0.operation = 'FLOORED_MODULO'
    y0.inputs[1].default_value = 2.0
    y0.location = (-850, -100)
    y0.parent = f_y
    links.new(inp.outputs["Y"], y0.inputs[0])

    div_y2 = nodes.new(type="ShaderNodeMath")
    div_y2.operation = 'DIVIDE'
    div_y2.inputs[1].default_value = 2.0
    div_y2.location = (-850, -250)
    div_y2.parent = f_y
    links.new(inp.outputs["Y"], div_y2.inputs[0])
    flr_y2 = nodes.new(type="ShaderNodeMath")
    flr_y2.operation = 'FLOOR'
    flr_y2.location = (-680, -250)
    flr_y2.parent = f_y
    links.new(div_y2.outputs["Value"], flr_y2.inputs[0])
    y1 = nodes.new(type="ShaderNodeMath")
    y1.operation = 'FLOORED_MODULO'
    y1.inputs[1].default_value = 2.0
    y1.location = (-510, -250)
    y1.parent = f_y
    links.new(flr_y2.outputs["Value"], y1.inputs[0])

    div_y4 = nodes.new(type="ShaderNodeMath")
    div_y4.operation = 'DIVIDE'
    div_y4.inputs[1].default_value = 4.0
    div_y4.location = (-850, -400)
    div_y4.parent = f_y
    links.new(inp.outputs["Y"], div_y4.inputs[0])
    flr_y4 = nodes.new(type="ShaderNodeMath")
    flr_y4.operation = 'FLOOR'
    flr_y4.location = (-680, -400)
    flr_y4.parent = f_y
    links.new(div_y4.outputs["Value"], flr_y4.inputs[0])
    y2 = nodes.new(type="ShaderNodeMath")
    y2.operation = 'FLOORED_MODULO'
    y2.inputs[1].default_value = 2.0
    y2.location = (-510, -400)
    y2.parent = f_y
    links.new(flr_y4.outputs["Value"], y2.inputs[0])

    # Interleaving
    sub0 = nodes.new(type="ShaderNodeMath")
    sub0.operation = 'SUBTRACT'
    sub0.location = (-250, 400)
    sub0.parent = f_b
    links.new(x0.outputs["Value"], sub0.inputs[0])
    links.new(y0.outputs["Value"], sub0.inputs[1])
    abs0 = nodes.new(type="ShaderNodeMath")
    abs0.operation = 'ABSOLUTE'
    abs0.location = (-80, 400)
    abs0.parent = f_b
    links.new(sub0.outputs["Value"], abs0.inputs[0])

    sub1 = nodes.new(type="ShaderNodeMath")
    sub1.operation = 'SUBTRACT'
    sub1.location = (-250, 250)
    sub1.parent = f_b
    links.new(x1.outputs["Value"], sub1.inputs[0])
    links.new(y1.outputs["Value"], sub1.inputs[1])
    abs1 = nodes.new(type="ShaderNodeMath")
    abs1.operation = 'ABSOLUTE'
    abs1.location = (-80, 250)
    abs1.parent = f_b
    links.new(sub1.outputs["Value"], abs1.inputs[0])

    sub2 = nodes.new(type="ShaderNodeMath")
    sub2.operation = 'SUBTRACT'
    sub2.location = (-250, 100)
    sub2.parent = f_b
    links.new(x2.outputs["Value"], sub2.inputs[0])
    links.new(y2.outputs["Value"], sub2.inputs[1])
    abs2 = nodes.new(type="ShaderNodeMath")
    abs2.operation = 'ABSOLUTE'
    abs2.location = (-80, 100)
    abs2.parent = f_b
    links.new(sub2.outputs["Value"], abs2.inputs[0])

    mul32 = nodes.new(type="ShaderNodeMath")
    mul32.operation = 'MULTIPLY'
    mul32.inputs[1].default_value = 32.0
    mul32.location = (90, 400)
    mul32.parent = f_b
    links.new(abs0.outputs["Value"], mul32.inputs[0])

    mul16 = nodes.new(type="ShaderNodeMath")
    mul16.operation = 'MULTIPLY'
    mul16.inputs[1].default_value = 16.0
    mul16.location = (90, -100)
    mul16.parent = f_b
    links.new(y0.outputs["Value"], mul16.inputs[0])

    mul8 = nodes.new(type="ShaderNodeMath")
    mul8.operation = 'MULTIPLY'
    mul8.inputs[1].default_value = 8.0
    mul8.location = (260, 250)
    mul8.parent = f_b
    links.new(abs1.outputs["Value"], mul8.inputs[0])

    mul4 = nodes.new(type="ShaderNodeMath")
    mul4.operation = 'MULTIPLY'
    mul4.inputs[1].default_value = 4.0
    mul4.location = (260, -250)
    mul4.parent = f_b
    links.new(y1.outputs["Value"], mul4.inputs[0])

    mul2 = nodes.new(type="ShaderNodeMath")
    mul2.operation = 'MULTIPLY'
    mul2.inputs[1].default_value = 2.0
    mul2.location = (430, 100)
    mul2.parent = f_b
    links.new(abs2.outputs["Value"], mul2.inputs[0])

    add1 = nodes.new(type="ShaderNodeMath")
    add1.operation = 'ADD'
    add1.location = (430, 350)
    add1.parent = f_b
    links.new(mul32.outputs["Value"], add1.inputs[0])
    links.new(mul16.outputs["Value"], add1.inputs[1])

    add2 = nodes.new(type="ShaderNodeMath")
    add2.operation = 'ADD'
    add2.location = (600, 300)
    add2.parent = f_b
    links.new(add1.outputs["Value"], add2.inputs[0])
    links.new(mul8.outputs["Value"], add2.inputs[1])

    add3 = nodes.new(type="ShaderNodeMath")
    add3.operation = 'ADD'
    add3.location = (770, 250)
    add3.parent = f_b
    links.new(add2.outputs["Value"], add3.inputs[0])
    links.new(mul4.outputs["Value"], add3.inputs[1])

    add4 = nodes.new(type="ShaderNodeMath")
    add4.operation = 'ADD'
    add4.location = (940, 200)
    add4.parent = f_b
    links.new(add3.outputs["Value"], add4.inputs[0])
    links.new(mul2.outputs["Value"], add4.inputs[1])

    add_v = nodes.new(type="ShaderNodeMath")
    add_v.operation = 'ADD'
    add_v.location = (1110, 150)
    add_v.parent = f_b
    links.new(add4.outputs["Value"], add_v.inputs[0])
    links.new(y2.outputs["Value"], add_v.inputs[1])

    add_half = nodes.new(type="ShaderNodeMath")
    add_half.operation = 'ADD'
    add_half.inputs[1].default_value = 0.5
    add_half.location = (1110, -50)
    add_half.parent = f_o
    links.new(add_v.outputs["Value"], add_half.inputs[0])

    div64 = nodes.new(type="ShaderNodeMath")
    div64.operation = 'DIVIDE'
    div64.inputs[1].default_value = 64.0
    div64.location = (1110, -200)
    div64.parent = f_o
    links.new(add_half.outputs["Value"], div64.inputs[0])
    links.new(div64.outputs["Value"], out.inputs["Normalized"])

    sub_half = nodes.new(type="ShaderNodeMath")
    sub_half.operation = 'SUBTRACT'
    sub_half.inputs[1].default_value = 0.5
    sub_half.location = (1110, -350)
    sub_half.parent = f_o
    links.new(div64.outputs["Value"], sub_half.inputs[0])
    links.new(sub_half.outputs["Value"], out.inputs["Centered"])

    return ng


def create_retro_dither_shader_fx():
    """Generates the master Retro_Dither_Shader_FX node group."""
    create_shader_bayer_4x4()
    create_shader_bayer_8x8()

    group_name = "Retro_Dither_Shader_FX"
    if group_name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[group_name])

    fx = bpy.data.node_groups.new(name=group_name, type="ShaderNodeTree")
    fx.use_fake_user = True

    # ---------------------------------------------------------
    # INTERFACE: PANELS & EASY SLIDERS
    # ---------------------------------------------------------
    fx.interface.new_socket(name="Color", in_out="INPUT", socket_type="NodeSocketColor")

    # Panel 1: Resolution & Grid
    p_grid = fx.interface.new_panel("Resolution & Grid")
    s_ps = fx.interface.new_socket(name="Pixel Size", in_out="INPUT", socket_type="NodeSocketInt", parent=p_grid)
    s_ps.default_value = 1
    s_ps.min_value = 1
    s_ps.max_value = 32
    s_ps.description = "Pixel block size (1 = native, 2-4 = chunky retro)"

    s_coord_mode = fx.interface.new_socket(name="Screen (1.0) / Object (0.0)", in_out="INPUT", socket_type="NodeSocketFloat", parent=p_grid)
    s_coord_mode.default_value = 1.0
    s_coord_mode.min_value = 0.0
    s_coord_mode.max_value = 1.0
    s_coord_mode.description = "1.0: Locked to screen-space window grid; 0.0: Anchored to 3D object surface UVs"

    s_rx = fx.interface.new_socket(name="Resolution X", in_out="INPUT", socket_type="NodeSocketFloat", parent=p_grid)
    s_rx.default_value = 300.0
    s_rx.min_value = 1.0
    s_rx.max_value = 4096.0

    s_ry = fx.interface.new_socket(name="Resolution Y", in_out="INPUT", socket_type="NodeSocketFloat", parent=p_grid)
    s_ry.default_value = 300.0
    s_ry.min_value = 1.0
    s_ry.max_value = 4096.0

    s_uv_scale = fx.interface.new_socket(name="Object UV Scale", in_out="INPUT", socket_type="NodeSocketFloat", parent=p_grid)
    s_uv_scale.default_value = 64.0
    s_uv_scale.min_value = 1.0
    s_uv_scale.max_value = 512.0

    # Panel 2: Dither Pattern
    p_dither = fx.interface.new_panel("Dither Pattern")
    s_mm = fx.interface.new_socket(name="Matrix Mode (0=4x4, 1=8x8)", in_out="INPUT", socket_type="NodeSocketInt", parent=p_dither)
    s_mm.default_value = 0
    s_mm.min_value = 0
    s_mm.max_value = 1
    s_mm.description = "0: Classic 4x4 matrix, 1: Smooth 64-level 8x8 matrix"

    s_ds = fx.interface.new_socket(name="Dither Strength", in_out="INPUT", socket_type="NodeSocketFloat", parent=p_dither)
    s_ds.default_value = 1.0
    s_ds.min_value = 0.0
    s_ds.max_value = 3.0

    # Panel 3: Tone Adjustments (Look)
    p_tone = fx.interface.new_panel("Tone Adjustments (Look)")
    s_br = fx.interface.new_socket(name="Brightness", in_out="INPUT", socket_type="NodeSocketFloat", parent=p_tone)
    s_br.default_value = 0.0
    s_br.min_value = -1.0
    s_br.max_value = 1.0

    s_ct = fx.interface.new_socket(name="Contrast", in_out="INPUT", socket_type="NodeSocketFloat", parent=p_tone)
    s_ct.default_value = 1.0
    s_ct.min_value = 0.0
    s_ct.max_value = 3.0

    s_gm = fx.interface.new_socket(name="Midtone Gamma", in_out="INPUT", socket_type="NodeSocketFloat", parent=p_tone)
    s_gm.default_value = 1.0
    s_gm.min_value = 0.1
    s_gm.max_value = 3.0

    # Panel 4: Color & Palette
    p_color = fx.interface.new_panel("Color & Palette")
    s_cm = fx.interface.new_socket(name="Color Mode (0=1Bit, 1=Levels, 2=RGB)", in_out="INPUT", socket_type="NodeSocketInt", parent=p_color)
    s_cm.default_value = 0
    s_cm.min_value = 0
    s_cm.max_value = 2

    s_cl = fx.interface.new_socket(name="Color Levels", in_out="INPUT", socket_type="NodeSocketInt", parent=p_color)
    s_cl.default_value = 4
    s_cl.min_value = 2
    s_cl.max_value = 32

    s_th = fx.interface.new_socket(name="1-Bit Threshold", in_out="INPUT", socket_type="NodeSocketFloat", parent=p_color)
    s_th.default_value = 0.5
    s_th.min_value = 0.0
    s_th.max_value = 1.0

    s_dk = fx.interface.new_socket(name="Dark Color", in_out="INPUT", socket_type="NodeSocketColor", parent=p_color)
    s_dk.default_value = (0.04, 0.02, 0.0, 1.0)

    s_lt = fx.interface.new_socket(name="Light Color", in_out="INPUT", socket_type="NodeSocketColor", parent=p_color)
    s_lt.default_value = (1.0, 0.72, 0.1, 1.0)

    # Panel 5: Output & Blend
    p_blend = fx.interface.new_panel("Output & Masking")
    s_mx = fx.interface.new_socket(name="Effect Mix (Dry/Wet)", in_out="INPUT", socket_type="NodeSocketFloat", parent=p_blend)
    s_mx.default_value = 1.0
    s_mx.min_value = 0.0
    s_mx.max_value = 1.0

    # Outputs
    fx.interface.new_socket(name="Color", in_out="OUTPUT", socket_type="NodeSocketColor")
    fx.interface.new_socket(name="Emission Shader", in_out="OUTPUT", socket_type="NodeSocketShader")
    fx.interface.new_socket(name="Dither Pattern", in_out="OUTPUT", socket_type="NodeSocketFloat")

    nodes = fx.nodes
    links = fx.links

    inp = nodes.new(type="NodeGroupInput")
    inp.location = (-1800, 0)
    out = nodes.new(type="NodeGroupOutput")
    out.location = (2750, 200)

    # Frames
    f1 = nodes.new(type="NodeFrame")
    f1.label = "1. Coordinate Space & Pixel Grid"
    f1.use_custom_color = True
    f1.color = (0.12, 0.22, 0.38)

    f2 = nodes.new(type="NodeFrame")
    f2.label = "2. Procedural Bayer Matrix"
    f2.use_custom_color = True
    f2.color = (0.1, 0.32, 0.32)

    f3 = nodes.new(type="NodeFrame")
    f3.label = "3. Tone Adjustments (Look)"
    f3.use_custom_color = True
    f3.color = (0.4, 0.25, 0.1)

    f4 = nodes.new(type="NodeFrame")
    f4.label = "4. Mode 0: 1-Bit Dither & Tint"
    f4.use_custom_color = True
    f4.color = (0.3, 0.15, 0.4)

    f5 = nodes.new(type="NodeFrame")
    f5.label = "5. Mode 1: Multi-Level Quantization"
    f5.use_custom_color = True
    f5.color = (0.15, 0.35, 0.2)

    f6 = nodes.new(type="NodeFrame")
    f6.label = "6. Mode 2: Multi-Bit RGB Quantization"
    f6.use_custom_color = True
    f6.color = (0.4, 0.15, 0.2)

    f7 = nodes.new(type="NodeFrame")
    f7.label = "7. Mode Selector & Blend"
    f7.use_custom_color = True
    f7.color = (0.2, 0.2, 0.25)

    # 1. Coordinates
    tex_coord = nodes.new(type="ShaderNodeTexCoord")
    tex_coord.location = (-1700, 250)
    tex_coord.parent = f1

    sep_win = nodes.new(type="ShaderNodeSeparateXYZ")
    sep_win.location = (-1500, 350)
    sep_win.parent = f1
    links.new(tex_coord.outputs["Window"], sep_win.inputs["Vector"])

    sep_uv = nodes.new(type="ShaderNodeSeparateXYZ")
    sep_uv.location = (-1500, 150)
    sep_uv.parent = f1
    links.new(tex_coord.outputs["UV"], sep_uv.inputs["Vector"])

    mul_win_x = nodes.new(type="ShaderNodeMath")
    mul_win_x.operation = 'MULTIPLY'
    mul_win_x.location = (-1320, 450)
    mul_win_x.parent = f1
    links.new(sep_win.outputs["X"], mul_win_x.inputs[0])
    links.new(inp.outputs["Resolution X"], mul_win_x.inputs[1])

    mul_win_y = nodes.new(type="ShaderNodeMath")
    mul_win_y.operation = 'MULTIPLY'
    mul_win_y.location = (-1320, 300)
    mul_win_y.parent = f1
    links.new(sep_win.outputs["Y"], mul_win_y.inputs[0])
    links.new(inp.outputs["Resolution Y"], mul_win_y.inputs[1])

    mul_uv_x = nodes.new(type="ShaderNodeMath")
    mul_uv_x.operation = 'MULTIPLY'
    mul_uv_x.location = (-1320, 150)
    mul_uv_x.parent = f1
    links.new(sep_uv.outputs["X"], mul_uv_x.inputs[0])
    links.new(inp.outputs["Object UV Scale"], mul_uv_x.inputs[1])

    mul_uv_y = nodes.new(type="ShaderNodeMath")
    mul_uv_y.operation = 'MULTIPLY'
    mul_uv_y.location = (-1320, 0)
    mul_uv_y.parent = f1
    links.new(sep_uv.outputs["Y"], mul_uv_y.inputs[0])
    links.new(inp.outputs["Object UV Scale"], mul_uv_y.inputs[1])

    mix_coord_x = nodes.new(type="ShaderNodeMix")
    mix_coord_x.data_type = 'FLOAT'
    mix_coord_x.location = (-1140, 300)
    mix_coord_x.parent = f1
    links.new(inp.outputs["Screen (1.0) / Object (0.0)"], mix_coord_x.inputs[0])
    links.new(mul_uv_x.outputs["Value"], mix_coord_x.inputs[2])
    links.new(mul_win_x.outputs["Value"], mix_coord_x.inputs[3])

    mix_coord_y = nodes.new(type="ShaderNodeMix")
    mix_coord_y.data_type = 'FLOAT'
    mix_coord_y.location = (-1140, 100)
    mix_coord_y.parent = f1
    links.new(inp.outputs["Screen (1.0) / Object (0.0)"], mix_coord_y.inputs[0])
    links.new(mul_uv_y.outputs["Value"], mix_coord_y.inputs[2])
    links.new(mul_win_y.outputs["Value"], mix_coord_y.inputs[3])

    div_px_x = nodes.new(type="ShaderNodeMath")
    div_px_x.operation = 'DIVIDE'
    div_px_x.location = (-960, 250)
    div_px_x.parent = f1
    links.new(mix_coord_x.outputs[0], div_px_x.inputs[0])
    links.new(inp.outputs["Pixel Size"], div_px_x.inputs[1])

    flr_px_x = nodes.new(type="ShaderNodeMath")
    flr_px_x.operation = 'FLOOR'
    flr_px_x.location = (-800, 250)
    flr_px_x.parent = f1
    links.new(div_px_x.outputs["Value"], flr_px_x.inputs[0])

    div_px_y = nodes.new(type="ShaderNodeMath")
    div_px_y.operation = 'DIVIDE'
    div_px_y.location = (-960, 100)
    div_px_y.parent = f1
    links.new(mix_coord_y.outputs[0], div_px_y.inputs[0])
    links.new(inp.outputs["Pixel Size"], div_px_y.inputs[1])

    flr_px_y = nodes.new(type="ShaderNodeMath")
    flr_px_y.operation = 'FLOOR'
    flr_px_y.location = (-800, 100)
    flr_px_y.parent = f1
    links.new(div_px_y.outputs["Value"], flr_px_y.inputs[0])

    # 2. Bayer Matrices
    b4 = nodes.new(type="ShaderNodeGroup")
    b4.node_tree = bpy.data.node_groups["Shader_Bayer_4x4"]
    b4.location = (-600, 200)
    b4.parent = f2
    links.new(flr_px_x.outputs["Value"], b4.inputs["X"])
    links.new(flr_px_y.outputs["Value"], b4.inputs["Y"])

    b8 = nodes.new(type="ShaderNodeGroup")
    b8.node_tree = bpy.data.node_groups["Shader_Bayer_8x8"]
    b8.location = (-600, 0)
    b8.parent = f2
    links.new(flr_px_x.outputs["Value"], b8.inputs["X"])
    links.new(flr_px_y.outputs["Value"], b8.inputs["Y"])

    sw_matrix = nodes.new(type="ShaderNodeMix")
    sw_matrix.data_type = 'FLOAT'
    sw_matrix.location = (-400, 100)
    sw_matrix.parent = f2
    links.new(inp.outputs["Matrix Mode (0=4x4, 1=8x8)"], sw_matrix.inputs[0])
    links.new(b4.outputs["Centered"], sw_matrix.inputs[2])
    links.new(b8.outputs["Centered"], sw_matrix.inputs[3])

    sw_norm = nodes.new(type="ShaderNodeMix")
    sw_norm.data_type = 'FLOAT'
    sw_norm.location = (-400, -100)
    sw_norm.parent = f2
    links.new(inp.outputs["Matrix Mode (0=4x4, 1=8x8)"], sw_norm.inputs[0])
    links.new(b4.outputs["Normalized"], sw_norm.inputs[2])
    links.new(b8.outputs["Normalized"], sw_norm.inputs[3])
    links.new(sw_norm.outputs[0], out.inputs["Dither Pattern"])

    mul_str = nodes.new(type="ShaderNodeMath")
    mul_str.operation = 'MULTIPLY'
    mul_str.location = (-200, 100)
    mul_str.parent = f2
    links.new(sw_matrix.outputs[0], mul_str.inputs[0])
    links.new(inp.outputs["Dither Strength"], mul_str.inputs[1])

    # 3. Tone Adjustments (Look)
    rgb_bw = nodes.new(type="ShaderNodeRGBToBW")
    rgb_bw.location = (-200, 400)
    rgb_bw.parent = f3
    links.new(inp.outputs["Color"], rgb_bw.inputs["Color"])

    inv_gamma = nodes.new(type="ShaderNodeMath")
    inv_gamma.operation = 'DIVIDE'
    inv_gamma.inputs[0].default_value = 1.0
    inv_gamma.location = (-30, 500)
    inv_gamma.parent = f3
    links.new(inp.outputs["Midtone Gamma"], inv_gamma.inputs[1])

    lum_gamma = nodes.new(type="ShaderNodeMath")
    lum_gamma.operation = 'POWER'
    lum_gamma.location = (140, 450)
    lum_gamma.parent = f3
    links.new(rgb_bw.outputs["Val"], lum_gamma.inputs[0])
    links.new(inv_gamma.outputs["Value"], lum_gamma.inputs[1])

    sub_half = nodes.new(type="ShaderNodeMath")
    sub_half.operation = 'SUBTRACT'
    sub_half.inputs[1].default_value = 0.5
    sub_half.location = (-30, 300)
    sub_half.parent = f3
    links.new(lum_gamma.outputs["Value"], sub_half.inputs[0])

    mul_cont = nodes.new(type="ShaderNodeMath")
    mul_cont.operation = 'MULTIPLY'
    mul_cont.location = (140, 300)
    mul_cont.parent = f3
    links.new(sub_half.outputs["Value"], mul_cont.inputs[0])
    links.new(inp.outputs["Contrast"], mul_cont.inputs[1])

    add_half_c = nodes.new(type="ShaderNodeMath")
    add_half_c.operation = 'ADD'
    add_half_c.inputs[1].default_value = 0.5
    add_half_c.location = (310, 300)
    add_half_c.parent = f3
    links.new(mul_cont.outputs["Value"], add_half_c.inputs[0])

    add_bright = nodes.new(type="ShaderNodeMath")
    add_bright.operation = 'ADD'
    add_bright.location = (480, 300)
    add_bright.parent = f3
    links.new(add_half_c.outputs["Value"], add_bright.inputs[0])
    links.new(inp.outputs["Brightness"], add_bright.inputs[1])

    clamp_tone = nodes.new(type="ShaderNodeClamp")
    clamp_tone.location = (650, 300)
    clamp_tone.parent = f3
    links.new(add_bright.outputs["Value"], clamp_tone.inputs["Value"])

    # 4. Mode 0: 1-Bit Dither & Tint
    add_dither_1bit = nodes.new(type="ShaderNodeMath")
    add_dither_1bit.operation = 'ADD'
    add_dither_1bit.location = (850, 600)
    add_dither_1bit.parent = f4
    links.new(clamp_tone.outputs["Result"], add_dither_1bit.inputs[0])
    links.new(mul_str.outputs["Value"], add_dither_1bit.inputs[1])

    step_1bit = nodes.new(type="ShaderNodeMath")
    step_1bit.operation = 'GREATER_THAN'
    step_1bit.location = (1020, 600)
    step_1bit.parent = f4
    links.new(add_dither_1bit.outputs["Value"], step_1bit.inputs[0])
    links.new(inp.outputs["1-Bit Threshold"], step_1bit.inputs[1])

    mix_1bit = nodes.new(type="ShaderNodeMix")
    mix_1bit.data_type = 'RGBA'
    mix_1bit.location = (1200, 600)
    mix_1bit.parent = f4
    links.new(step_1bit.outputs["Value"], mix_1bit.inputs[0])
    links.new(inp.outputs["Dark Color"], mix_1bit.inputs[6])
    links.new(inp.outputs["Light Color"], mix_1bit.inputs[7])

    # 5. Mode 1: Multi-Level Quantization
    sub_one = nodes.new(type="ShaderNodeMath")
    sub_one.operation = 'SUBTRACT'
    sub_one.inputs[1].default_value = 1.0
    sub_one.location = (850, 100)
    sub_one.parent = f5
    links.new(inp.outputs["Color Levels"], sub_one.inputs[0])

    div_levels = nodes.new(type="ShaderNodeMath")
    div_levels.operation = 'DIVIDE'
    div_levels.location = (850, -50)
    div_levels.parent = f5
    links.new(mul_str.outputs["Value"], div_levels.inputs[0])
    links.new(sub_one.outputs["Value"], div_levels.inputs[1])

    add_dither_multi = nodes.new(type="ShaderNodeMath")
    add_dither_multi.operation = 'ADD'
    add_dither_multi.location = (1020, 200)
    add_dither_multi.parent = f5
    links.new(clamp_tone.outputs["Result"], add_dither_multi.inputs[0])
    links.new(div_levels.outputs["Value"], add_dither_multi.inputs[1])

    mul_steps = nodes.new(type="ShaderNodeMath")
    mul_steps.operation = 'MULTIPLY'
    mul_steps.location = (1190, 200)
    mul_steps.parent = f5
    links.new(add_dither_multi.outputs["Value"], mul_steps.inputs[0])
    links.new(sub_one.outputs["Value"], mul_steps.inputs[1])

    add_half_steps = nodes.new(type="ShaderNodeMath")
    add_half_steps.operation = 'ADD'
    add_half_steps.inputs[1].default_value = 0.5
    add_half_steps.location = (1360, 200)
    add_half_steps.parent = f5
    links.new(mul_steps.outputs["Value"], add_half_steps.inputs[0])

    flr_steps = nodes.new(type="ShaderNodeMath")
    flr_steps.operation = 'FLOOR'
    flr_steps.location = (1530, 200)
    flr_steps.parent = f5
    links.new(add_half_steps.outputs["Value"], flr_steps.inputs[0])

    div_back = nodes.new(type="ShaderNodeMath")
    div_back.operation = 'DIVIDE'
    div_back.location = (1700, 200)
    div_back.parent = f5
    links.new(flr_steps.outputs["Value"], div_back.inputs[0])
    links.new(sub_one.outputs["Value"], div_back.inputs[1])

    clamp_multi = nodes.new(type="ShaderNodeClamp")
    clamp_multi.location = (1870, 200)
    clamp_multi.parent = f5
    links.new(div_back.outputs["Value"], clamp_multi.inputs["Value"])

    comb_multi = nodes.new(type="ShaderNodeCombineColor")
    comb_multi.location = (2040, 200)
    comb_multi.parent = f5
    links.new(clamp_multi.outputs["Result"], comb_multi.inputs["Red"])
    links.new(clamp_multi.outputs["Result"], comb_multi.inputs["Green"])
    links.new(clamp_multi.outputs["Result"], comb_multi.inputs["Blue"])

    # 6. Mode 2: Multi-Bit RGB Quantization
    sep_rgb = nodes.new(type="ShaderNodeSeparateColor")
    sep_rgb.location = (850, -300)
    sep_rgb.parent = f6
    links.new(inp.outputs["Color"], sep_rgb.inputs["Color"])

    def build_channel_quant(chan_sock, y_off):
        add_d = nodes.new(type="ShaderNodeMath")
        add_d.operation = 'ADD'
        add_d.location = (1020, y_off)
        add_d.parent = f6
        links.new(chan_sock, add_d.inputs[0])
        links.new(div_levels.outputs["Value"], add_d.inputs[1])

        mul_l = nodes.new(type="ShaderNodeMath")
        mul_l.operation = 'MULTIPLY'
        mul_l.location = (1190, y_off)
        mul_l.parent = f6
        links.new(add_d.outputs["Value"], mul_l.inputs[0])
        links.new(sub_one.outputs["Value"], mul_l.inputs[1])

        add_h = nodes.new(type="ShaderNodeMath")
        add_h.operation = 'ADD'
        add_h.inputs[1].default_value = 0.5
        add_h.location = (1360, y_off)
        add_h.parent = f6
        links.new(mul_l.outputs["Value"], add_h.inputs[0])

        flr = nodes.new(type="ShaderNodeMath")
        flr.operation = 'FLOOR'
        flr.location = (1530, y_off)
        flr.parent = f6
        links.new(add_h.outputs["Value"], flr.inputs[0])

        div_l = nodes.new(type="ShaderNodeMath")
        div_l.operation = 'DIVIDE'
        div_l.location = (1700, y_off)
        div_l.parent = f6
        links.new(flr.outputs["Value"], div_l.inputs[0])
        links.new(sub_one.outputs["Value"], div_l.inputs[1])

        cl = nodes.new(type="ShaderNodeClamp")
        cl.location = (1870, y_off)
        cl.parent = f6
        links.new(div_l.outputs["Value"], cl.inputs["Value"])
        return cl.outputs["Result"]

    qr = build_channel_quant(sep_rgb.outputs["Red"], -200)
    qg = build_channel_quant(sep_rgb.outputs["Green"], -350)
    qb = build_channel_quant(sep_rgb.outputs["Blue"], -500)

    comb_rgb = nodes.new(type="ShaderNodeCombineColor")
    comb_rgb.location = (2040, -350)
    comb_rgb.parent = f6
    links.new(qr, comb_rgb.inputs["Red"])
    links.new(qg, comb_rgb.inputs["Green"])
    links.new(qb, comb_rgb.inputs["Blue"])

    # 7. Mode Selector & Blend
    clamp_cm_01 = nodes.new(type="ShaderNodeClamp")
    clamp_cm_01.location = (2120, 450)
    clamp_cm_01.parent = f7
    links.new(inp.outputs["Color Mode (0=1Bit, 1=Levels, 2=RGB)"], clamp_cm_01.inputs["Value"])

    sw_01 = nodes.new(type="ShaderNodeMix")
    sw_01.data_type = 'RGBA'
    sw_01.location = (2260, 450)
    sw_01.parent = f7
    links.new(clamp_cm_01.outputs["Result"], sw_01.inputs[0])
    links.new(mix_1bit.outputs[2], sw_01.inputs[6])
    links.new(comb_multi.outputs["Color"], sw_01.inputs[7])

    sub_cm = nodes.new(type="ShaderNodeMath")
    sub_cm.operation = 'SUBTRACT'
    sub_cm.inputs[1].default_value = 1.0
    sub_cm.location = (2120, 300)
    sub_cm.parent = f7
    links.new(inp.outputs["Color Mode (0=1Bit, 1=Levels, 2=RGB)"], sub_cm.inputs[0])

    clamp_cm_12 = nodes.new(type="ShaderNodeClamp")
    clamp_cm_12.location = (2260, 300)
    clamp_cm_12.parent = f7
    links.new(sub_cm.outputs["Value"], clamp_cm_12.inputs["Value"])

    sw_final = nodes.new(type="ShaderNodeMix")
    sw_final.data_type = 'RGBA'
    sw_final.location = (2400, 350)
    sw_final.parent = f7
    links.new(clamp_cm_12.outputs["Result"], sw_final.inputs[0])
    links.new(sw_01.outputs[2], sw_final.inputs[6])
    links.new(comb_rgb.outputs["Color"], sw_final.inputs[7])

    # Dry/Wet Blend
    mix_dry_wet = nodes.new(type="ShaderNodeMix")
    mix_dry_wet.data_type = 'RGBA'
    mix_dry_wet.location = (2550, 350)
    mix_dry_wet.parent = f7
    links.new(inp.outputs["Effect Mix (Dry/Wet)"], mix_dry_wet.inputs[0])
    links.new(inp.outputs["Color"], mix_dry_wet.inputs[6])
    links.new(sw_final.outputs[2], mix_dry_wet.inputs[7])

    # Emission Shader Output
    emiss = nodes.new(type="ShaderNodeEmission")
    emiss.inputs["Strength"].default_value = 1.0
    emiss.location = (2550, 150)
    emiss.parent = f7
    links.new(mix_dry_wet.outputs[2], emiss.inputs["Color"])

    links.new(mix_dry_wet.outputs[2], out.inputs["Color"])
    links.new(emiss.outputs["Emission"], out.inputs["Emission Shader"])

    return fx


def create_or_update_dither_material(mat_name="Retro_Dither_Live_Material"):
    """Creates a ready-to-use live viewport dither material."""
    create_retro_dither_shader_fx()

    mat = bpy.data.materials.get(mat_name)
    if mat is None:
        mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()

    nodes = tree.nodes
    links = tree.links

    # Frame containers
    f_shading = nodes.new(type="NodeFrame")
    f_shading.label = "Surface Lighting (Principled BSDF)"
    f_shading.use_custom_color = True
    f_shading.color = (0.15, 0.25, 0.45)

    f_dither = nodes.new(type="NodeFrame")
    f_dither.label = "Retro Dither FX (Adjust Sliders Here)"
    f_dither.use_custom_color = True
    f_dither.color = (0.45, 0.25, 0.15)

    f_out = nodes.new(type="NodeFrame")
    f_out.label = "Material Output"
    f_out.use_custom_color = True
    f_out.color = (0.25, 0.2, 0.35)

    # 1. BSDF Shading
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.location = (-650, 150)
    bsdf.inputs["Base Color"].default_value = (0.9, 0.35, 0.1, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.4
    bsdf.parent = f_shading

    s2rgb = nodes.new(type="ShaderNodeShaderToRGB")
    s2rgb.location = (-380, 150)
    s2rgb.parent = f_shading
    links.new(bsdf.outputs["BSDF"], s2rgb.inputs["Shader"])

    # 2. Dither Group Node
    dither_fx = nodes.new(type="ShaderNodeGroup")
    dither_fx.name = "Retro Dither FX"
    dither_fx.node_tree = bpy.data.node_groups["Retro_Dither_Shader_FX"]
    dither_fx.location = (-100, 150)
    dither_fx.width = 300
    dither_fx.parent = f_dither

    # Default resolution and pixel size
    dither_fx.inputs["Resolution X"].default_value = 300.0
    dither_fx.inputs["Resolution Y"].default_value = 300.0
    dither_fx.inputs["Pixel Size"].default_value = 1

    links.new(s2rgb.outputs["Color"], dither_fx.inputs["Color"])

    # 3. Material Output
    mat_out = nodes.new(type="ShaderNodeOutputMaterial")
    mat_out.location = (300, 150)
    mat_out.parent = f_out
    links.new(dither_fx.outputs["Emission Shader"], mat_out.inputs["Surface"])

    return mat


def setup_shader_dither_scene(target_obj_name="Suzanne"):
    """Configures the scene to use the live viewport shader dither system."""
    scene = bpy.context.scene

    # Ensure View Transform is 'Standard' for exact sRGB color palette reproduction
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'

    # Set EEVEE and ensure viewport rendered shading is enabled
    scene.render.engine = 'BLENDER_EEVEE'
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'RENDERED'

    # Bypass compositor so rendering is 100% shader-driven
    if scene.compositing_node_group:
        tree = scene.compositing_node_group
        tree.links.clear()
        rl = [n for n in tree.nodes if n.type == 'R_LAYERS']
        out = [n for n in tree.nodes if n.type == 'GROUP_OUTPUT']
        viewer = [n for n in tree.nodes if n.type == 'VIEWER']
        if rl and out:
            tree.links.new(rl[0].outputs["Image"], out[0].inputs["Image"])
        if rl and viewer:
            tree.links.new(rl[0].outputs["Image"], viewer[0].inputs["Image"])

    # Create and assign material to target object
    mat = create_or_update_dither_material()
    obj = bpy.data.objects.get(target_obj_name)
    if obj:
        obj.data.materials.clear()
        obj.data.materials.append(mat)
        print(f"Assigned Retro_Dither_Live_Material to {obj.name}!")

    print("Live Viewport Shader Dither System successfully configured!")


if __name__ == "__main__":
    setup_shader_dither_scene()
