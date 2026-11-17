"""Mercat Pure Fresh · montaje 3D sobre BARCELONA_BASE.blend (Rambla de Catalunya 32) y renders.
Uso: Blender -b <BARCELONA_BASE.blend> --python build_mercat.py -- <outdir> [cams...] [--draft]
Orientación del modelo: +Y = fachada a la calle (escaparate 301 y ventana de la alcoba), entrada por el chaflán A (+X).
Conversión al plano Samplia (1600 px): X = -5.37 + (px-118)/137 ; Y = 2.72 - (py-118)/137."""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
DRAFT = "--draft" in argv
argv = [a for a in argv if a != "--draft"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = argv[0] if argv else os.path.join(ROOT, "assets", "renders")
CAMS = argv[1:] or ["R1_CATA", "R2_QUEST", "R3_MIRADA", "R4_FACHADA", "R0_PLANTA"]
TEX = os.path.join(ROOT, "3D", "tex"); ASS = os.path.join(ROOT, "assets")
os.makedirs(OUTDIR, exist_ok=True)
rnd = random.Random(11)
sc = bpy.context.scene
COL = bpy.data.collections.new("PF_MERCAT"); sc.collection.children.link(COL)

# ---------- materiales ----------
def bsdf(m):
    m.use_nodes = True; nt = m.node_tree
    for n in nt.nodes:
        if n.type == "BSDF_PRINCIPLED": return n
    out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None) or nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled"); nt.links.new(b.outputs[0], out.inputs["Surface"]); return b
def srgb(c): return tuple(((v / 255) ** 2.2) for v in c) + (1,)
def mcol(name, rgb, rough=0.6, metal=0.0, emit=0.0, trans=0.0):
    m = bpy.data.materials.new(name); b = bsdf(m)
    b.inputs["Base Color"].default_value = srgb(rgb); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit: b.inputs["Emission Color"].default_value = srgb(rgb); b.inputs["Emission Strength"].default_value = emit
    if trans: b.inputs["Transmission Weight"].default_value = trans
    return m
def mimg(name, file, rough=0.55, emit=0.0, alpha=False, folder=TEX):
    m = bpy.data.materials.new(name); b = bsdf(m); nt = m.node_tree
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(folder, file))
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = rough
    if emit: nt.links.new(t.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = emit
    if alpha: nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    return m

ORANGE=(226,96,27); BROWN=(74,38,24); PEA=(92,154,46); YEL=(242,194,48)
M = {
 "cream": mcol("PF_crema", (236, 224, 208), 0.8), "orange": mcol("PF_naranja", ORANGE, 0.5),
 "brown": mcol("PF_marron", BROWN, 0.5), "wood": mcol("PF_madera", (150, 98, 58), 0.45),
 "pea": mcol("PF_verde", PEA, 0.7), "felt": mcol("PF_fieltro", (70, 120, 40), 0.95),
 "ceramic": mcol("PF_ceramica", (250, 248, 244), 0.15), "kib_dry": mcol("PF_seco", (170, 115, 60), 0.8),
 "kib_fresh": mcol("PF_fresh", (150, 70, 40), 0.55), "black": mcol("PF_negro", (25, 25, 25), 0.35, 0.6),
 "steel": mcol("PF_acero", (200, 200, 205), 0.25, 1.0), "glass": mcol("PF_cristal", (235, 245, 250), 0.03),
 "ghost": mcol("PF_figura", (232, 228, 224), 0.7), "dog1": mcol("PF_perro_caramelo", (190, 120, 60), 0.75),
 "dog2": mcol("PF_perro_negro", (45, 38, 34), 0.7), "dog3": mcol("PF_perro_crema", (225, 200, 160), 0.8),
 "nose": mcol("PF_nariz", (18, 14, 12), 0.3), "yel": mcol("PF_amarillo", YEL, 0.6),
 "rug": mcol("PF_alfombra", (238, 220, 196), 0.95), "softbox": mcol("PF_softbox", (255, 250, 240), 0.5, 0, 1.5),
 "coldlight": mcol("PF_frio", (170, 220, 255), 0.5, 0, 2.0), "red": mcol("PF_manzana", (200, 40, 35), 0.4),
}
for k, f in [("wall_carne", "wall_carne.jpg"), ("counter", "counter_front.jpg"), ("bridge", "bridge.jpg"),
             ("cabina", "hdr_cabina.jpg"), ("gancho", "hdr_gancho.jpg"), ("muro_hdr", "hdr_muro.jpg"),
             ("perso_hdr", "hdr_personaliza.jpg"), ("plinko", "plinko.jpg"), ("mosaic", "mosaic.jpg"),
             ("backdrop", "backdrop.jpg"), ("sachet", "sachet.jpg"), ("band_o", "bandana_o.jpg"),
             ("band_g", "bandana_g.jpg"), ("reto", "hdr_reto.jpg"), ("alc_st", "alcove_street.jpg")]:
    M[k] = mimg("PF_" + k, f)
M["led"] = mimg("PF_led", "led.jpg", emit=1.4)
for k, f in [("awning", "awning.png"), ("cata", "cata_mat.png"), ("huerta", "huerta.png"),
             ("recep", "recepcion.png"), ("dots", "dots.png"), ("escap", "escaparate.png")]:
    M[k] = mimg("PF_" + k, f, alpha=True)
M["pack"] = mimg("PF_pack", "pack-salmon.png", alpha=True, folder=ASS)

# ---------- geometría ----------
def link(o):
    for c in o.users_collection: c.objects.unlink(o)
    COL.objects.link(o); return o
def box(name, c, s, mat, rz=0.0, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=c, rotation=(0, 0, rz))
    o = bpy.context.object; o.name = name; o.scale = s
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel: md = o.modifiers.new("bv", "BEVEL"); md.width = bevel; md.segments = 3
    o.data.materials.append(mat); return link(o)
def cyl(name, c, r, h, mat, rot=(0, 0, 0), verts=40):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=c, rotation=rot)
    o = bpy.context.object; o.name = name; o.data.materials.append(mat); bpy.ops.object.shade_smooth(); return link(o)
def sph(name, c, r, mat, s=(1, 1, 1), rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=r, location=c, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = s; o.data.materials.append(mat); bpy.ops.object.shade_smooth(); return link(o)
def quad(name, p, mat):
    me = bpy.data.meshes.new(name); me.from_pydata([Vector(v) for v in p], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new()
    for i, l in enumerate(me.loops): uv.data[i].uv = [(0, 0), (1, 0), (1, 1), (0, 1)][l.vertex_index]
    o = bpy.data.objects.new(name, me); COL.objects.link(o); me.materials.append(mat); return o
def wall_panel(name, a, b, z0, z1, mat, off=0.012):
    """a = extremo izquierdo visto por el espectador; el panel se separa 'off' hacia él."""
    a, b = Vector((a[0], a[1], 0)), Vector((b[0], b[1], 0))
    d = (b - a).normalized(); n = Vector((d.y, -d.x, 0))
    a2, b2 = a + n * off, b + n * off
    return quad(name, [(a2.x, a2.y, z0), (b2.x, b2.y, z0), (b2.x, b2.y, z1), (a2.x, a2.y, z1)], mat)
def floor_quad(name, c, w, h, mat, rz=0.0, z=0.004):
    o = quad(name, [(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)], mat)
    o.location = (c[0], c[1], z); o.rotation_euler = (0, 0, rz); return o
def path_dots(p0, p1):
    c = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2); L = math.dist(p0, p1)
    floor_quad("PF_puntos", c, L, 0.06, M["dots"], math.atan2(p1[1] - p0[1], p1[0] - p0[0]), 0.003)
def look(o, target):
    o.rotation_euler = (Vector(target) - o.location).to_track_quat("-Z", "Y").to_euler()
def group(name, parts, loc, heading):
    root = bpy.data.objects.new(name, None); COL.objects.link(root)
    for p in parts: p.parent = root
    root.location = loc; root.rotation_euler = (0, 0, math.radians(heading)); return root

def dog(name, loc, heading, mat, pose="stand", s=1.0):
    P = []; leg = 0.30 * s
    if pose == "sit":
        P.append(sph(name, (0, 0, 0.30 * s), 0.17 * s, mat, (1.15, 0.95, 1.35)))
        P.append(sph(name, (0.10 * s, 0, 0.43 * s), 0.13 * s, mat, (1, 1, 1.2)))
        hx, hz = 0.15 * s, 0.67 * s
        for sy in (-1, 1):
            P.append(cyl(name, (0.16 * s, sy * 0.07 * s, 0.13 * s), 0.035 * s, 0.26 * s, mat))
            P.append(sph(name, (-0.03 * s, sy * 0.12 * s, 0.14 * s), 0.10 * s, mat, (1.4, 0.7, 0.9)))
        P.append(cyl(name, (-0.24 * s, 0, 0.05 * s), 0.025 * s, 0.25 * s, mat, (0, math.radians(80), 0)))
    else:
        P.append(sph(name, (0, 0, leg + 0.12 * s), 0.16 * s, mat, (1.9, 0.95, 1.0)))
        hx, hz = (0.33 * s, 0.13 * s) if pose == "sniff" else (0.30 * s, leg + 0.24 * s)
        for sx in (-1, 1):
            for sy in (-1, 1):
                P.append(cyl(name, (sx * 0.19 * s, sy * 0.08 * s, leg / 2 + 0.02 * s), 0.035 * s, leg, mat))
        P.append(cyl(name, (-0.36 * s, 0, leg + 0.24 * s), 0.025 * s, 0.28 * s, mat, (0, math.radians(-40), 0)))
        nx, nz = (hx + 0.18 * s) / 2, (hz + leg + 0.16 * s) / 2
        ln = math.hypot(hx - 0.18 * s, hz - leg - 0.16 * s)
        P.append(cyl(name, (nx, 0, nz), 0.07 * s, ln + 0.08 * s, mat, (0, math.atan2(hx - 0.18 * s, hz - leg - 0.16 * s), 0)))
    P.append(sph(name, (hx, 0, hz), 0.105 * s, mat, (1.15, 0.95, 0.95)))
    P.append(sph(name, (hx + 0.13 * s, 0, hz - 0.035 * s), 0.06 * s, mat, (1.6, 0.8, 0.7)))
    P.append(sph(name, (hx + 0.225 * s, 0, hz - 0.02 * s), 0.022 * s, M["nose"]))
    for sy in (-1, 1):
        P.append(sph(name, (hx - 0.03 * s, sy * 0.105 * s, hz - 0.05 * s), 0.065 * s, mat, (0.5, 0.22, 1.15), (sy * 0.25, 0, 0)))
        P.append(sph(name, (hx + 0.085 * s, sy * 0.045 * s, hz + 0.03 * s), 0.014 * s, M["nose"]))
    return group(name, P, loc if len(loc) == 3 else (loc[0], loc[1], 0), heading)
def person(name, loc, heading, pose="stand", h=1.72):
    k = h / 1.72; P = []; g = M["ghost"]
    if pose == "sit":
        for sy in (-1, 1):
            P.append(cyl(name, (0.20 * k, sy * 0.1 * k, 0.48 * k), 0.07 * k, 0.42 * k, g, (0, math.radians(90), 0)))
            P.append(cyl(name, (0.40 * k, sy * 0.1 * k, 0.24 * k), 0.06 * k, 0.48 * k, g))
        tz = 0.48 * k
    else:
        for sy in (-1, 1): P.append(cyl(name, (0, sy * 0.1 * k, 0.43 * k), 0.07 * k, 0.86 * k, g))
        tz = 0.86 * k
    P.append(cyl(name, (0, 0, tz + 0.29 * k), 0.17 * k, 0.56 * k, g))
    P.append(sph(name, (0, 0, tz + 0.55 * k), 0.17 * k, g, (0.9, 1.25, 0.6)))
    P.append(sph(name, (0, 0, tz + 0.02 * k), 0.17 * k, g, (0.9, 1.1, 0.5)))
    P.append(sph(name, (0.02 * k, 0, tz + 0.76 * k), 0.11 * k, g, (1, 0.9, 1.15)))
    for sy in (-1, 1): P.append(cyl(name, (0.06 * k, sy * 0.22 * k, tz + 0.30 * k), 0.05 * k, 0.56 * k, g, (0, math.radians(-12), 0)))
    return group(name, P, loc if len(loc) == 3 else (loc[0], loc[1], 0), heading)

# cristales transparentes (los del modelo y los nuevos)
for mname in ("LS_CRISTAL", "PF_cristal"):
    m = bpy.data.materials.get(mname)
    if m:
        b = bsdf(m); b.inputs["Base Color"].default_value = (0.9, 0.95, 1.0, 1); b.inputs["Alpha"].default_value = 0.12
        b.inputs["Roughness"].default_value = 0.0
        try: m.surface_render_method = "BLENDED"
        except Exception: pass

# zócalo corporativo en todas las paredes: marrón abajo, filete naranja, crema y banda naranja arriba
def band_material():
    m = bpy.data.materials.new("PF_pared_banda"); b = bsdf(m); nt = m.node_tree
    geo = nt.nodes.new("ShaderNodeNewGeometry"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    div = nt.nodes.new("ShaderNodeMath"); div.operation = "DIVIDE"; div.inputs[1].default_value = 2.6
    ramp = nt.nodes.new("ShaderNodeValToRGB"); cr = ramp.color_ramp; cr.interpolation = "CONSTANT"
    stops = [(0.0, (107, 58, 36)), (0.354, ORANGE), (0.377, (246, 234, 218)), (0.777, ORANGE), (0.862, (246, 238, 228))]
    cr.elements[0].position, cr.elements[0].color = stops[0][0], srgb(stops[0][1])
    cr.elements[1].position, cr.elements[1].color = stops[1][0], srgb(stops[1][1])
    for pos, c in stops[2:]:
        e = cr.elements.new(pos); e.color = srgb(c)
    nt.links.new(geo.outputs["Position"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], div.inputs[0])
    nt.links.new(div.outputs[0], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.7
    return m
M["cream"] = band_material()
# ---------- base: paredes crema, sin mostrador verde original ----------
it = bpy.data.objects["INTERIOR TIENDA"]
it.data.materials.append(M["cream"]); ci = len(it.data.materials) - 1
for f in it.data.polygons:
    if abs(f.normal.z) < 0.3: f.material_index = ci
if "Box125" in bpy.data.objects: bpy.data.objects["Box125"].hide_render = True

# ===== 1 · RECEPCIÓN (A1) · agua junto a A4 =====
wall_panel("PF_recepcion_A1", (1.05, 1.91), (2.67, 1.28), 0.0, 2.22, M["recep"])
rz = math.atan2(1.28 - 1.91, 2.67 - 1.05)
box("PF_recepcion_mostrador", (1.741, 1.288, 0.5), (1.2, 0.45, 1.0), M["brown"], rz, 0.01)
box("PF_recepcion_sobre", (1.741, 1.288, 1.015), (1.26, 0.5, 0.03), M["wood"], rz)
for i in range(9):
    sph("PF_fruta", (1.45 + i * 0.07, 1.36 - i * 0.027, 1.07), 0.035, M["red"] if i % 3 else M["pea"])
cyl("PF_agua", (3.9, -0.45, 0.035), 0.13, 0.07, M["steel"])

# ===== 2 · L'OBRADOR: cabina de frío en el escaparate + puente =====
ccx, ccy = 0.40, 1.98
box("PF_cabina_base", (ccx, ccy, 0.075), (1.0, 1.0, 0.15), M["brown"])
for dx in (-0.48, 0.48):
    for dy in (-0.48, 0.48):
        box("PF_cabina_poste", (ccx + dx, ccy + dy, 1.1), (0.05, 0.05, 2.0), M["brown"])
box("PF_cabina_techo", (ccx, ccy, 2.13), (1.02, 1.02, 0.12), M["brown"])
wall_panel("PF_cabina_rotulo_in", (ccx + 0.5, ccy - 0.515), (ccx - 0.5, ccy - 0.515), 2.075, 2.185, M["cabina"], off=0.0)
wall_panel("PF_cabina_rotulo_in", (ccx - 0.5, ccy - 0.515), (ccx + 0.5, ccy - 0.515), 2.075, 2.185, M["cabina"], off=0.0)
wall_panel("PF_cabina_rotulo_out", (ccx + 0.5, ccy + 0.515), (ccx - 0.5, ccy + 0.515), 2.075, 2.185, M["cabina"], off=0.0)
for a, b in [((ccx - 0.48, ccy - 0.48), (ccx + 0.48, ccy - 0.48)), ((ccx + 0.48, ccy - 0.48), (ccx + 0.48, ccy + 0.48)),
             ((ccx - 0.48, ccy + 0.48), (ccx - 0.48, ccy - 0.48)), ((ccx + 0.48, ccy + 0.48), (ccx - 0.48, ccy + 0.48))]:
    wall_panel("PF_cabina_cristal", a, b, 0.15, 2.07, M["glass"], off=0.0)
vegm = [M["orange"], M["pea"], M["red"], M["yel"]]
for i in range(50):
    sph("PF_ficha", (ccx + rnd.uniform(-0.4, 0.4), ccy + rnd.uniform(-0.4, 0.4), rnd.uniform(0.35, 2.0)),
        rnd.uniform(0.025, 0.045), rnd.choice(vegm + [M["kib_fresh"]]), (1, 1, 0.35), (rnd.random(), rnd.random(), 0))
box("PF_cabina_luz", (ccx, ccy, 2.065), (0.8, 0.8, 0.01), M["coldlight"])
person("PF_jugador_cabina", (ccx, ccy, 0.15), -90)
# pack gigante de doble cara mirando a la calle y hacia dentro
for side, rot in (("calle", 0.0), ("dentro", math.pi)):
    q = quad("PF_pack_gigante_" + side, [(-0.42, 0, 0), (0.42, 0, 0), (0.42, 0, 1.55), (-0.42, 0, 1.55)], M["pack"])
    q.location = (-1.2, 2.3 + (0.005 if side == "calle" else -0.005), 0.0); q.rotation_euler = (0, 0, rot)
box("PF_pack_peana", (-1.2, 2.3, 0.04), (0.95, 0.35, 0.08), M["brown"])
# vinilos del escaparate (legibles desde la calle)
wall_panel("PF_vinilo_toldo", (1.01, 2.545), (-1.94, 2.545), 2.25, 2.75, M["awning"], off=0.0)
wall_panel("PF_vinilo_texto", (1.01, 2.545), (-1.94, 2.545), 0.08, 0.5, M["escap"], off=0.0)
# trasera del fotomatón hacia la calle (ventana de la alcoba)
wall_panel("PF_alcoba_calle", (-3.45, 2.66), (-5.15, 2.66), 0.0, 2.2, M["alc_st"], off=0.0)
# puente agility SECO → FRESCO
bxc, byc = -0.75, 0.55
r1 = box("PF_puente_rampa_a", (bxc - 0.56, byc, 0.13), (0.45, 0.4, 0.03), M["brown"]); r1.rotation_euler = (0, math.radians(33), 0)
r2 = box("PF_puente_rampa_b", (bxc + 0.56, byc, 0.13), (0.45, 0.4, 0.03), M["orange"]); r2.rotation_euler = (0, math.radians(-33), 0)
box("PF_puente_tablero", (bxc, byc, 0.25), (0.75, 0.4, 0.04), M["brown"])
floor_quad("PF_puente_grafica", (bxc, byc), 0.75, 0.4, M["bridge"], 0, 0.272)
for dx in (-0.3, 0.3):
    for dy in (-0.17, 0.17): cyl("PF_puente_pata", (bxc + dx, byc + dy, 0.12), 0.02, 0.24, M["brown"])
dog("PF_perro_puente", (bxc + 0.05, byc, 0.27), 180, M["dog1"], "stand", 0.8)
person("PF_guia_puente", (bxc - 0.55, byc + 0.55), -20)

# ===== 3 · PARADA DE LA HUERTA (columna E) =====
wall_panel("PF_huerta_E3", (-3.13, 1.61), (-2.44, 1.61), 0.0, 2.22, M["huerta"])
box("PF_balda_olfato", (-2.785, 1.48, 0.98), (0.66, 0.26, 0.03), M["wood"])
for i in range(5):
    box("PF_caja_olfato", (-3.04 + i * 0.128, 1.47, 1.06), (0.11, 0.2, 0.13), M["wood"] if i % 2 else M["brown"], 0, 0.006)
cyl("PF_snuffle", (-2.51, 0.84, 0.06), 0.6, 0.12, M["felt"], verts=64)
for i in range(70):
    a = rnd.random() * 2 * math.pi; r = 0.55 * rnd.random() ** 0.5
    sph("PF_bola_huerta", (-2.51 + r * math.cos(a), 0.84 + r * math.sin(a), 0.14), 0.04 + rnd.random() * 0.02, rnd.choice(vegm))
dog("PF_perro_huerta", (-2.2, 0.55), 150, M["dog3"], "sniff", 0.85)
person("PF_dueno_huerta", (-1.75, 1.15), -160)

# ===== 4 · EL RETRATISTA =====
wall_panel("PF_fondo_foto", (-5.15, 2.64), (-3.45, 2.64), 0.0, 2.22, M["backdrop"], off=0.0)
floor_quad("PF_alfombra_foto", (-4.3, 1.85), 1.7, 1.2, M["rug"])
box("PF_banco", (-4.65, 1.95, 0.22), (0.45, 0.45, 0.44), M["wood"], 0, 0.02)
person("PF_dueno_mirada", (-4.65, 1.92, 0.0), 0, "sit")
dog("PF_perro_mirada", (-3.95, 1.92), 180, M["dog2"], "sit", 1.05)
for i, ang in enumerate((0, 120, 240)):
    a = math.radians(ang)
    cyl("PF_tripode", (-4.3 + 0.12 * math.cos(a), 0.45 + 0.12 * math.sin(a), 0.6), 0.012, 1.25, M["black"],
        (0.18 * math.sin(a), -0.18 * math.cos(a), 0))
box("PF_camara", (-4.3, 0.45, 1.25), (0.14, 0.1, 0.1), M["black"])
cyl("PF_objetivo", (-4.3, 0.52, 1.25), 0.035, 0.08, M["black"], (math.radians(90), 0, 0))
bpy.ops.mesh.primitive_torus_add(location=(-4.3, 0.45, 1.25), rotation=(math.radians(90), 0, 0), major_radius=0.2, minor_radius=0.02)
ring = bpy.context.object; ring.name = "PF_aro_luz"; ring.data.materials.append(M["softbox"]); link(ring)
for sx in ():
    cyl("PF_pie_luz", (sx, 0.85, 0.85), 0.012, 1.7, M["black"])
    sb = box("PF_softbox", (sx, 0.85, 1.75), (0.45, 0.08, 0.6), M["softbox"])
    sb.rotation_euler = (0, 0, math.atan2(1.95 - 0.85, -4.3 - sx) - math.pi / 2)
wall_panel("PF_muro_mosaico", (-5.37, -0.55), (-5.37, 2.0), 0.22, 1.95, M["mosaic"])
wall_panel("PF_muro_titulo", (-5.37, -0.55), (-5.37, 2.0), 1.97, 2.2, M["muro_hdr"])
box("PF_mesa_perso", (-3.63, -0.46, 0.45), (1.3, 0.45, 0.9), M["orange"], 0, 0.01)
box("PF_mesa_perso_top", (-3.63, -0.46, 0.915), (1.34, 0.49, 0.03), M["wood"])
wall_panel("PF_perso_titulo", (-2.95, -0.70), (-4.31, -0.70), 1.55, 1.85, M["perso_hdr"])
for m, dx in [(M["orange"], -0.45), (M["ceramic"], -0.25), (M["pea"], -0.05)]:
    cyl("PF_comedero", (-3.63 + dx, -0.42, 0.965), 0.08, 0.07, m)
for i, m in enumerate((M["band_o"], M["band_g"])):
    t = quad("PF_bandana", [(0, 0, 0), (0.3, 0, 0), (0.15, 0.22, 0), (0.15, 0.22, 0)], m); t.location = (-3.4 + i * 0.32, -0.6, 0.935)
box("PF_grabadora", (-3.1, -0.48, 1.04), (0.3, 0.25, 0.22), M["black"], 0, 0.01)

# ===== 5 · PARADA DE LA CARNE en la pared del fondo (B4) =====
wall_panel("PF_pared_carne", (1.05, -2.70), (-1.75, -2.70), 0.0, 2.22, M["wall_carne"])
cx = -0.35
box("PF_carne_mostrador", (cx, -2.38, 0.475), (2.0, 0.58, 0.95), M["wood"])
wall_panel("PF_carne_frontal", (cx + 1.0, -2.088), (cx - 1.0, -2.088), 0.0, 0.95, M["counter"], off=0.0)
box("PF_carne_encimera", (cx, -2.37, 0.97), (2.06, 0.64, 0.04), M["brown"])
box("PF_led", (cx, -2.645, 1.48), (1.44, 0.05, 0.82), M["black"])
wall_panel("PF_led_pantalla", (cx + 0.69, -2.618), (cx - 0.69, -2.618), 1.09, 1.87, M["led"], off=0.0)
quad("PF_toldo_carne", [(cx + 1.12, -1.96, 1.95), (cx - 1.12, -1.96, 1.95), (cx - 1.12, -2.68, 2.17), (cx + 1.12, -2.68, 2.17)], M["awning"])
for px in (cx - 1.02, cx + 1.02): cyl("PF_poste", (px, -2.0, 1.47), 0.022, 0.96, M["brown"])
cyl("PF_bascula_base", (cx - 0.55, -2.32, 1.04), 0.13, 0.1, M["steel"])
cyl("PF_bascula_plato", (cx - 0.55, -2.32, 1.14), 0.17, 0.02, M["steel"])
for i in range(6):
    box("PF_sobre", (cx + 0.5 + (i % 3) * 0.13, -2.37 - (i // 3) * 0.05, 1.07), (0.1, 0.02, 0.14), M["sachet"])
floor_quad("PF_cata_alfombra", (cx, -1.30), 1.5, 1.5, M["cata"], math.pi)
for bx, kib in ((cx + 0.40, "kib_dry"), (cx - 0.40, "kib_fresh")):
    cyl("PF_cuenco", (bx, -1.42, 0.035), 0.12, 0.07, M["ceramic"])
    cyl("PF_cuenco_comida", (bx, -1.42, 0.068), 0.10, 0.012, M[kib])
cyl("PF_bowlcam_barra", (cx, -1.35, 2.42), 0.015, 0.36, M["black"])
box("PF_bowlcam", (cx, -1.35, 2.22), (0.12, 0.09, 0.08), M["black"])
dog("PF_perro_cata", (cx - 0.15, -0.88), -112, M["dog1"], "stand", 1.0)
person("PF_tendero", (cx - 0.75, -2.55), 75)
person("PF_duena_cata", (cx - 1.15, -0.95), -40)


# ===== 6 · PREMIOS junto a la salida (B2 y chaflán B1) =====
box("PF_plinko", (2.38, -2.57, 0.9), (1.04, 0.26, 1.8), M["brown"], 0, 0.01)
wall_panel("PF_plinko_frente", (1.86, -2.438), (2.90, -2.438), 0.02, 1.78, M["plinko"], off=0.0)
gx, gy = 3.3, -1.3
box("PF_gancho_base", (gx, gy, 0.45), (0.78, 0.78, 0.9), M["orange"], 0, 0.01)
for dx in (-0.37, 0.37):
    for dy in (-0.37, 0.37): box("PF_gancho_poste", (gx + dx, gy + dy, 1.3), (0.04, 0.04, 0.8), M["brown"])
for a, b in [((gx - 0.37, gy + 0.37), (gx + 0.37, gy + 0.37)), ((gx - 0.37, gy - 0.37), (gx - 0.37, gy + 0.37)),
             ((gx + 0.37, gy + 0.37), (gx + 0.37, gy - 0.37))]:
    wall_panel("PF_gancho_cristal", a, b, 0.9, 1.7, M["glass"], off=0.0)
box("PF_gancho_techo", (gx, gy, 1.78), (0.8, 0.8, 0.16), M["orange"])
wall_panel("PF_gancho_rotulo", (gx - 0.4, gy + 0.405), (gx + 0.4, gy + 0.405), 1.71, 1.85, M["gancho"], off=0.0)
wall_panel("PF_gancho_rotulo2", (gx - 0.405, gy - 0.4), (gx - 0.405, gy + 0.4), 1.71, 1.85, M["gancho"], off=0.0)
for i in range(16):
    box("PF_premio", (gx + rnd.uniform(-0.28, 0.28), gy + rnd.uniform(-0.28, 0.28), 0.95 + rnd.uniform(0, 0.08)),
        (0.1, 0.14, 0.02), M["sachet"], rnd.uniform(0, 3))
cyl("PF_gancho_cable", (gx, gy, 1.55), 0.005, 0.3, M["steel"])


# ===== paneles de marca en el resto de paredes =====
for k in ("brand_B1", "brand_A5", "brand_C3", "brand_corto_o", "brand_corto_b", "brand_verde", "brand_B2"):
    M[k] = mimg("PF_" + k, k + ".jpg")
for nm, a, b, k in [
    ("B1", (4.93, -0.71), (2.94, -2.70), "brand_B1"), ("A5", (4.20, 0.02), (4.93, -0.71), "brand_A5"),
    ("C3", (-2.92, -1.84), (-2.92, -0.70), "brand_C3"), ("esc_der", (1.05, 2.58), (1.05, 1.91), "brand_corto_o"),
    ("esc_izq", (-1.96, 2.09), (-1.96, 2.58), "brand_corto_b"), ("E_frente_der", (-2.44, 2.09), (-1.96, 2.09), "brand_corto_b"),
    ("E4", (-2.44, 1.61), (-2.44, 2.09), "brand_verde"), ("E2", (-3.13, 2.15), (-3.13, 1.61), "brand_verde"),
    ("B2", (2.94, -2.70), (1.83, -2.70), "brand_B2"), ("C2", (-2.43, -1.84), (-2.97, -1.84), "brand_corto_b"),
    ("C1", (-2.43, -2.70), (-2.43, -1.84), "brand_corto_o")]:
    wall_panel("PF_marca_" + nm, a, b, 0.0, 2.22, M[k])

# camino de puntos (recorrido antihorario)
for p0, p1 in [((3.2, 0.55), (2.2, 0.75)), ((1.2, 0.9), (0.2, 1.1)), ((-0.2, 1.0), (-1.6, 1.1)),
               ((-3.2, 0.55), (-4.0, 0.9)), ((-3.6, 0.05), (-1.8, -0.6)), ((0.7, -1.2), (1.9, -1.7)), ((2.6, -0.9), (3.1, -0.3))]:
    path_dots(p0, p1)

# ---------- luces ----------
def area(name, loc, size, energy, color=(1.0, 0.9, 0.8)):
    ld = bpy.data.lights.new(name, "AREA"); ld.size = size; ld.energy = energy; ld.color = color
    o = bpy.data.objects.new(name, ld); COL.objects.link(o); o.location = loc; return o
area("PF_luz_carne", (cx, -1.4, 2.45), 1.6, 110)
area("PF_luz_huerta", (-2.6, 1.0, 2.45), 1.2, 70)
area("PF_luz_foto", (-4.3, 1.5, 2.45), 1.4, 80)
area("PF_luz_obrador", (-0.4, 1.2, 2.45), 1.8, 90)
area("PF_luz_premios", (2.7, -1.6, 2.45), 1.4, 70)
pl = bpy.data.lights.new("PF_frio_cabina", "POINT"); pl.energy = 40; pl.color = (0.6, 0.85, 1.0)
po = bpy.data.objects.new("PF_frio_cabina", pl); COL.objects.link(po); po.location = (ccx, ccy, 1.6)

# fondo de calle luminoso tras el escaparate (solo vistas interiores)
SKY = quad("PF_calle_fondo", [(8, 7, -1), (-9, 7, -1), (-9, 7, 6), (8, 7, 6)], mcol("PF_calle", (205, 215, 225), 0.9, 0, 1.2))
# ---------- cámaras ----------
def cam(name, loc, target, lens):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.clip_start = 0.05; cd.clip_end = 80
    o = bpy.data.objects.new(name, cd); COL.objects.link(o); o.location = loc; look(o, target); return o
CAMOBJ = {
 "R1_CATA": cam("R1_CATA", (0.95, 0.35, 1.5), (-0.6, -2.4, 0.95), 19),
 "R2_QUEST": cam("R2_QUEST", (1.6, -1.6, 1.7), (-1.5, 1.45, 0.75), 15),
 "R3_MIRADA": cam("R3_MIRADA", (-2.35, -0.25, 1.55), (-4.75, 1.45, 1.0), 15),
 "R0_PLANTA": cam("R0_PLANTA", (-0.3, -4.6, 10.5), (-0.3, 0.2, 0.0), 24),
 "R4_FACHADA": cam("R4_FACHADA", (0.9, 9.2, 1.65), (-1.35, 2.6, 1.45), 22),
}

# ---------- motor ----------
sc.render.engine = "BLENDER_EEVEE"; ee = sc.eevee
for attr, val in [("taa_render_samples", 16 if DRAFT else 128), ("use_raytracing", True), ("use_shadows", True)]:
    try: setattr(ee, attr, val)
    except Exception: pass
sc.render.resolution_x, sc.render.resolution_y = (960, 540) if DRAFT else (1920, 1080)
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 88
try: sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
except Exception: pass
sc.view_settings.exposure = -0.25

if not DRAFT:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "3D", "BCN_PURE_FRESH.blend"), copy=True)
    print("SAVED")

def strip_ceiling():
    me = it.data; bm = bmesh.new(); bm.from_mesh(me)
    W = it.matrix_world
    kill = [f for f in bm.faces if min((W @ v.co).z for v in f.verts) > 2.15]
    bmesh.ops.delete(bm, geom=kill, context="FACES"); bm.to_mesh(me); bm.free()
    for o in bpy.data.objects:
        if o.type == "MESH" and not o.name.startswith("PF_"):
            zs = [(o.matrix_world @ Vector(c)).z for c in o.bound_box]
            if min(zs) > 2.15 or o.name in ("CAJA EXTERIOR", "FACHADA", "NEGRO", "CRISTALES", "ACERA", "Line006"):
                o.hide_render = True
    for o in COL.objects:
        if o.name.startswith(("PF_bowlcam", "PF_vinilo_toldo")): o.hide_render = True

order = [c for c in CAMS if c != "R0_PLANTA"] + (["R0_PLANTA"] if "R0_PLANTA" in CAMS else [])
for name in order:
    if name == "R0_PLANTA":
        strip_ceiling()
    sc.view_settings.exposure = {"R3_MIRADA": -0.7, "R1_CATA": -0.45, "R2_QUEST": -0.35, "R4_FACHADA": 0.0, "R0_PLANTA": 0.0}.get(name, -0.3)
    w = sc.world or bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    if name in ("R4_FACHADA", "R0_PLANTA"):
        bg.inputs[0].default_value = (0.78, 0.82, 0.88, 1); bg.inputs[1].default_value = 0.8
    SKY.hide_render = name == "R4_FACHADA"
    sc.render.film_transparent = name == "R4_FACHADA"
    sc.render.image_settings.file_format = "PNG" if name == "R4_FACHADA" else "JPEG"
    if name == "R4_FACHADA": sc.render.image_settings.color_mode = "RGBA"
    else: sc.render.image_settings.color_mode = "RGB"
    sc.camera = CAMOBJ[name]
    sc.render.filepath = os.path.join(OUTDIR, name + (".png" if name == "R4_FACHADA" else ".jpg"))
    bpy.ops.render.render(write_still=True)
    print("RENDER_OK", name)
