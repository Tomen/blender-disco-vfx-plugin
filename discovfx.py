bl_info = {
    "name": "Disco VFX",
    "author": "Tommi Enenkel",
    "version": (0, 1),
    "blender": (2, 90, 0),
    "location": "View3D > Sidebar",
    "description": "Your own VFX Studio in Blender",
    "warning": "",
    "doc_url": "",
    "category": "VFX",
}


import bpy
import random
import mathutils
import math


def image_sequence_resolve_all(filepath):
    import os

    basedir, filename = os.path.split(filepath)
    filename_noext, ext = os.path.splitext(filename)

    from string import digits
    if isinstance(filepath, bytes):
        digits = digits.encode()
    filename_nodigits = filename_noext.rstrip(digits)

    if len(filename_nodigits) == len(filename_noext):
        # input isn't from a sequence
        return []

    return [
        f.path
        for f in os.scandir(basedir)
        if f.is_file() and
           f.name.startswith(filename_nodigits) and
           f.name.endswith(ext) and
           f.name[len(filename_nodigits):-len(ext) if ext else -1].isdigit()
    ]


class DiscoProps(bpy.types.PropertyGroup):
    sourcePath: bpy.props.StringProperty(subtype="FILE_PATH", default="/Users/tommi/Downloads/Wait a minute who are you Greenscreen Kazoo Kid Me.mp4")   
    prekeyPath: bpy.props.StringProperty(subtype="FILE_PATH", default="/Users/tommi/Documents/Blender/Renders/tmp/") 


class DISCO_PT_main_panel(bpy.types.Panel):
    
    bl_label = "Disco!"
    bl_idname = "DISCO_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Disco VFX'

    def draw(self, context):
        props = context.window_manager.disco_props
        layout = self.layout
        layout.label(text = "Compositing")
        layout.prop(props, "sourcePath")
        layout.prop(props, "prekeyPath")
        layout.operator("disco.prepare_prekey")
        layout.operator("disco.render_prekey")
        layout.operator("disco.place_prekey")
        layout.label(text = "Housekeeping")
        layout.operator("disco.clear_scene")
    
class ClearSceneOperator(bpy.types.Operator):
    bl_label = "Clear Scene"
    bl_idname = "disco.clear_scene"    
    
    def execute(self, context):
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        bpy.ops.outliner.orphans_purge()
        return {'FINISHED'}


class PreparePrekeyOperator(bpy.types.Operator):
    bl_label = "Prepare Prekeyed Card"
    bl_idname = "disco.prepare_prekey" 
    
    def execute(self, context):
        props = context.window_manager.disco_props
        
        scene = bpy.data.scenes.new(name='Prekey')
        bpy.context.window.scene = scene
        #bpy.ops.scene.new(type='NEW')
        #bpy.context.scene.name = "Prekey"
        scene.use_nodes = True
        nodes = scene.node_tree.nodes
        links = scene.node_tree.links
        # Delete the unused initial node
        nodes.remove(nodes["Render Layers"])
        compositeOutputNode = nodes["Composite"]        
        # Add image input node
        imageInputNode = nodes.new("CompositorNodeImage")
        imageInputNode.location = (-250, 400)
        image = bpy.data.images.load(filepath = props.sourcePath)
        imageInputNode.image = image
        imageInputNode.frame_duration = image.frame_duration
        scene.frame_end = image.frame_duration

        # Add Keying node
        keyingNode = nodes.new("CompositorNodeKeying")
        keyingNode.location = (0, 400)
        keyingNode.inputs[1].default_value = (0,0.1,0,1) 
        # Link it up
        links.new(imageInputNode.outputs[0], keyingNode.inputs[0])
        links.new(keyingNode.outputs[0], compositeOutputNode.inputs[0])
        # Preview node
        previewNode = nodes.new("CompositorNodeViewer")
        previewNode.location = (250, 600)
        links.new(keyingNode.outputs[0], previewNode.inputs[0])
        
        # Render the images 
        scene.render.resolution_x = image.size[0]
        scene.render.resolution_y = image.size[1]
        scene.render.filepath = props.prekeyPath
        #bpy.ops.render.render(write_still = True)
        
        return {'FINISHED'}
    
    
class RenderPrekeyOperator(bpy.types.Operator):
    bl_label = "Render Prekeyed Card"
    bl_idname = "disco.render_prekey" 
    
    def execute(self, context):
        scene = bpy.data.scenes.new(name='Prekey')
        bpy.context.window.scene = scene
        bpy.ops.render.render(write_still = True)
        
        return {'FINISHED'}

class PlacePrekeyOperator(bpy.types.Operator):
    bl_label = "Place Prekeyed Card"
    bl_idname = "disco.place_prekey" 
    
    def execute(self, context):
        props = context.window_manager.disco_props
        
        # Load Image
        image_files = image_sequence_resolve_all(props.prekeyPath + "0.png")
        image = bpy.data.images.load(filepath = image_files[0], check_existing=True)
        image.source = "SEQUENCE"

        # Create an object
        bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))        
        plane = bpy.context.active_object
        px, py = image.size
        y = 1
        x = px / py * y
        plane.dimensions = x, y, 0.0
        plane.rotation_euler.x = math.pi/2
        
        # Create the material
        material = bpy.data.materials.new(name="Card")
        material.blend_method = "BLEND"
        material.use_nodes = True
        plane.active_material = material        
        # Prepare editing the node network
        nodes = plane.active_material.node_tree.nodes
        links = plane.active_material.node_tree.links
        nodes.remove(nodes["Principled BSDF"])
        materialOutputNode = nodes["Material Output"]  
        # Add Image Texture
        imageTextureNode = nodes.new("ShaderNodeTexImage")
        imageTextureNode.location = (-500, 400)
        imageTextureNode.image = image
        imageTextureNode.image_user.frame_duration = len(image_files)
        imageTextureNode.image_user.use_auto_refresh = True
        bpy.context.scene.frame_end = max(bpy.context.scene.frame_end, image.frame_duration)        
        # Emission Shader
        emissionNode = nodes.new("ShaderNodeEmission")
        emissionNode.location = (-250, 0)
        # Transparent BSDF
        transparentNode = nodes.new("ShaderNodeBsdfTransparent")
        transparentNode.location = (-250, 400)
        # Mix Shader
        mixNode = nodes.new("ShaderNodeMixShader")
        mixNode.location = (0, 400)
        
        links.new(imageTextureNode.outputs[0], emissionNode.inputs[0])
        links.new(imageTextureNode.outputs[1], mixNode.inputs[0])
        links.new(transparentNode.outputs[0], mixNode.inputs[1])
        links.new(emissionNode.outputs[0], mixNode.inputs[2])
        links.new(mixNode.outputs[0], materialOutputNode.inputs[0])
        
        return {'FINISHED'}


classes = [
    DiscoProps,
    DISCO_PT_main_panel,
    ClearSceneOperator,
    PreparePrekeyOperator,
    RenderPrekeyOperator,
    PlacePrekeyOperator]
 
 
 
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.disco_props = bpy.props.PointerProperty(type=DiscoProps)

 
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.WindowManager.disco_props
 
 
if __name__ == "__main__":
    register()