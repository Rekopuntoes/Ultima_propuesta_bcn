import bpy, json
from mathutils import Vector
out={'objs':[], 'scene':{}}
sc=bpy.context.scene
out['scene']={'engine':sc.render.engine,'res':[sc.render.resolution_x,sc.render.resolution_y],'unit':sc.unit_settings.system,'scale':sc.unit_settings.scale_length,'camera':sc.camera.name if sc.camera else None}
for o in bpy.data.objects:
    bb=[o.matrix_world @ Vector(c) for c in o.bound_box] if o.type in('MESH','CURVE','FONT') else [o.matrix_world.translation]
    mn=[round(min(v[i] for v in bb),2) for i in range(3)]; mx=[round(max(v[i] for v in bb),2) for i in range(3)]
    d={'n':o.name,'t':o.type,'min':mn,'max':mx,'col':[c.name for c in o.users_collection],'hide':o.hide_render}
    if o.type=='MESH': d['mats']=[m.name for m in o.data.materials if m]; d['v']=len(o.data.vertices)
    if o.type=='CAMERA': d['rot']=[round(x,3) for x in o.rotation_euler]; d['lens']=o.data.lens
    if o.type=='LIGHT': d['lt']=o.data.type; d['e']=o.data.energy
    out['objs'].append(d)
print('JSON>>'+json.dumps(out))
