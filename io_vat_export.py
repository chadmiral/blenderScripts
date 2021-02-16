import bpy

# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator
from addon_utils import check, paths, enable # to use existing fbx exporter addon

from collections import defaultdict
import numpy as np

import os

# there's gotta be a built-in way to do this w/ numpy I havent found yet
def remap(value, low1, high1, low2, high2):
    return low2 + (value - low1) * (high2 - low2) / (high1 - low1)

# compute power of two greater than or equal to n
def next_power_of_2(n):
 
    # decrement n (to handle cases when n itself
    # is a power of 2)
    n = n - 1
 
    # do till only one bit is left
    while n & n - 1:
        n = n & n - 1  # unset rightmost bit
 
    # n is now a power of two (less than n)
 
    # return next power of 2
    return n << 1

aabb = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    
def expand_aabb(xyz):
    for c in range(3):
        if xyz[c] < aabb[0][c]:
            aabb[0][c] = xyz[c]
        if xyz[c] > aabb[1][c]:
            aabb[1][c] = xyz[c]


# write offset data to a texture and save to disk
def writeOffsetTexture(offsets, file_path, round_up = True):
    w = next_power_of_2(offsets.shape[0]) if round_up else offset.shape[0]
    h = offsets.shape[1]
    
    offsets = np.pad(offsets, ((0,w-offsets.shape[0]),(0,0),(0,0)), 'edge')
    
    #print(offsets.shape)
    
    channels = offsets.shape[2]

    img = bpy.data.images.new("OffsetTex", width=w, height=h)
    pixels = [None] * w * h
    for x in range(w):
        for y in range(h):
            r = remap(offsets[x][y][0], aabb[0][0], aabb[1][0], 0.0, 1.0)
            g = remap(offsets[x][y][1], aabb[0][1], aabb[1][1], 0.0, 1.0)
            b = remap(offsets[x][y][2], aabb[0][2], aabb[1][2], 0.0, 1.0)
            a = 1.0

            pixels[(y * w) + x] = [r, g, b, a]
    
    # flatten pixels
    pixels = [chan for px in pixels for chan in px]
    
    img.pixels = pixels
    
    # write to disk
    img.filepath_raw = file_path
    img.file_format = 'PNG'
    #img.alpha_mode = 'CHANNEL_PACKED'
    #img.depth = 16
    img.save()

def writeFBX(obj, file_path):
    #duplicate object and remove all modifiers
    
    bpy.ops.export_scene.fbx(filepath=file_path,
                             use_selection=True,
                             global_scale=0.1,
                             use_mesh_modifiers=True,
                             object_types={'MESH'},
                             bake_anim=False,
                             axis_forward='Y',
                             axis_up='Z')
                             
            
def assignVertexColors(obj, round_up = True):
    if 'Col' not in obj.data.vertex_colors.keys():
        obj.data.vertex_colors.new(name='Col')
        
    col = obj.data.vertex_colors['Col']
    polygons = obj.data.polygons
    vertices = obj.data.vertices
    
    vertex_map = defaultdict(list)
    for poly in polygons:
        for v_ix, l_ix in zip(poly.vertices, poly.loop_indices):
            vertex_map[v_ix].append(l_ix)
    
    # if we are rounding up the texture dims we also need to round up the
    # vertex colors so everything lines up.
    tex_w = len(vertex_map)
    if round_up:
        tex_w = next_power_of_2(len(vertex_map))
        
    #print("vertex_map: %d" % len(vertex_map))
    #print("tex_w: %d" % tex_w)
    #print(vertex_map)
    
    for v_ix, l_ixs in vertex_map.items():
        for l_ix in l_ixs:
            x = v_ix / tex_w #+ 0.5 * (1.0 / tex_w) #add half-pixel offset to center sample in the shader
            col.data[l_ix].color = (x, x, x, 1)
            #print(str(v_ix) + ": " + str(x) + ", " + str(vertices[v_ix].co))

def writeDebugCurves(anim_tracks):
    for t in range(anim_tracks.shape[1]):
        #print(t)
        curveData = bpy.data.curves.new('debug' + str(t), type='CURVE')
        curveData.dimensions = '3D'
        curveData.resolution_u = 2
        
        polyline = curveData.splines.new('POLY')
        polyline.points.add(len(anim_tracks[t]) - 1)
        for i, coord in enumerate(anim_tracks[t]):
            x,y,z = coord
            polyline.points[i].co = (x, y, z, 1)
            
        curveOB = bpy.data.objects.new('debugCurve' + str(t), curveData)
        curveData.bevel_depth = 0.01
        
        scene.collection.objects.link(curveOB)
        

def collectVertexOffsets(obj, scene):  
    ref_verts = obj.data.vertices #reference vertex positions (unskinned)
    offset_matrix = []
    
    # create an array of evaluated (modifiers applied) meshes at each frame
    eval_meshes = []
    for f in range(scene.frame_start, bpy.context.scene.frame_end + 1):
        scene.frame_set(f)
        
        # create a new mesh w/ all modifiers applied
        deps_graph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(deps_graph)
        eval_meshes.append(bpy.data.meshes.new_from_object(eval_obj))
    
    #print("eval_meshes: " + str(len(eval_meshes)))
    for v in ref_verts:
        #print("vidx: " + str(v.index) + " - " + str(v.co))
        anim_frames = []
        for f in range(scene.frame_start, scene.frame_end + 1):
            eval_mesh = eval_meshes[f - scene.frame_start]
            new_xyz = eval_meshes[f - scene.frame_start].vertices[v.index].co
            old_xyz = v.co
            
            expand_aabb(list(new_xyz))
            anim_frames.append(new_xyz)
        offset_matrix.append(anim_frames)
        #print(anim_frames)
            
    
    # clean up objects
    for em in eval_meshes:
        bpy.data.meshes.remove(em)
    
    return np.array(offset_matrix)


bl_info = {
    "name": "VAT Animation Exporter",
    "author": "Chandra Foxglove",
    "version": (0,1,0),
    "blender": (2, 80, 0),
    "location": "File > Import-Export",
    "description": "Export animated mesh to VAT (Vertex Animated Texture)",
    "category": "Import-Export",
}


class VATExporter(bpy.types.Operator, ExportHelper):
    """Export an animated mesh as a Vertex Animation Texture"""
    
    bl_idname = "vat.export"
    bl_label = "Export as VAT"
    bl_options = { 'PRESET' }
    
    filename_ext = ".png" #needed by the ExportHelper base class
    
    round_up: BoolProperty(
        name="Force Power of Two",
        description="Round output texture dimensions to nearest power of two.",
        default=True,
    )
    
    def execute(self, context):
        scene = context.scene
        obj = context.selected_objects[0]
        
        root_filepath = os.path.splitext(self.filepath)[0]
        
        # Do all the things!!!
        assignVertexColors(obj)
        anim_tracks = collectVertexOffsets(obj, scene)
        #writeDebugCurves(anim_tracks)
        writeOffsetTexture(anim_tracks, self.filepath, self.round_up)
        writeFBX(obj, root_filepath + ".fbx")
        print("Bounds: " + str(aabb))

        return {'FINISHED'}
    

# properties panel
class VAT_PT_options(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = 'Properties'
    bl_parent_id = "FILE_PT_operator"
    
    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
    
        return operator.bl_idname == "EXPORT_SCENE_OT_vat"
    
    
    def draw(self, context):
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.
    
            sfile = context.space_data
            operator = sfile.active_operator
    
            col = layout.column(heading="Limit to")
            col.prop(operator, 'use_selection')
    
            col = layout.column(heading="Objects as", align=True)
            col.prop(operator, 'use_blen_objects')
            col.prop(operator, 'group_by_object')
            col.prop(operator, 'group_by_material')
    
            layout.separator()
    
            layout.prop(operator, 'use_animation')
    
    
def menu_func(self, context):
    self.layout.operator(VATExporter.bl_idname, text="Vertex Animated Texture")
    
    
classes = (
    VATExporter,
    VAT_PT_options
)
    
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_export.append(menu_func)

    
def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func)
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
if __name__ == "__main__":
    register()