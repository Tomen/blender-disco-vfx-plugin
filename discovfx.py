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


class DiscoProps(bpy.types.PropertyGroup):
    sourcePath: bpy.props.StringProperty(subtype="FILE_PATH", default="/Users/tommi/Downloads/Wait a minute who are you Greenscreen Kazoo Kid Me.mp4")   
    targetPath: bpy.props.StringProperty(subtype="FILE_PATH", default="/Users/tommi/Documents/Blender/Renders/tmp/") 


class DISCO_PT_main_panel(bpy.types.Panel):
    
    bl_label = "Disco!"
    bl_idname = "DISCO_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Disco VFX'

    def draw(self, context):
        props = context.window_manager.disco_props
        layout = self.layout
        box = layout.box()
        box.label(text = "Compositing")
        box.prop(props, "sourcePath")
        box.prop(props, "targetPath")
        box.prop(props, "color")
        box.operator("disco.prekey")
        layout.label(text = "Playground")
        layout.operator("disco.delete_all_objects")
        layout.operator("disco.add_5x5")
        layout.operator("disco.add_color_material")
        layout.operator("disco.add_random_material")


class AddColorMaterialOperator(bpy.types.Operator):
    bl_label = "Add Color Shader"
    bl_idname = "disco.add_color_material"
    
    color: bpy.props.FloatVectorProperty(name= "Color", subtype= 'COLOR_GAMMA' , size=4, default= (0,0,0,1))

    
    def execute(self, context):
        
        # Create Material
        material_basic = bpy.data.materials.new(name= "Disco")
        material_basic.use_nodes = True
        
        # Principled BSDF
        principled_node = material_basic.node_tree.nodes.get('Principled BSDF')
        principled_node.inputs[7].default_value = 0.08
        
        # Color Node
        rgb_node = material_basic.node_tree.nodes.new('ShaderNodeRGB')
        rgb_node.location = (-250, 0)
        rgb_node.outputs[0].default_value = self.color
        
        # Connect it
        link = material_basic.node_tree.links.new
        link(rgb_node.outputs[0], principled_node.inputs[0])
        
        # Assign the material
        bpy.context.object.active_material = material_basic
    
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AddRandomMaterialOperator(bpy.types.Operator):
    bl_label = "Add Random Shader"
    bl_idname = "disco.add_random_material"
    
    def execute(self, context):
        c = mathutils.Color()
        c.hsv = random.random(), random.uniform(0.9, 1), 1
        bpy.ops.disco.add_color_material(color = (c.r, c.g, c.b, 1))
        return {'FINISHED'}
    

class Generate5x5Operator(bpy.types.Operator):
    bl_label = "Add 5x5"
    bl_idname = "disco.add_5x5"    
    
    def execute(self, context):
        for x in range(5):
            for y in range(5):
                location = (x, y, 0)
                bpy.ops.mesh.primitive_plane_add(size = 1, location = location)
                bpy.ops.object.select_all(action='SELECT')
                bpy.ops.disco.add_random_material()
        bpy.ops.view3d.view_selected()    
        return {'FINISHED'}
    
class DeleteAllObjectsOperator(bpy.types.Operator):
    bl_label = "Delete All Objects"
    bl_idname = "disco.delete_all_objects"    
    
    def execute(self, context):
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        return {'FINISHED'}


class PrekeyOperator(bpy.types.Operator):
    bl_label = "Create Prekeyed Cards"
    bl_idname = "disco.prekey" 
    
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
        scene.render.filepath = props.targetPath
        #bpy.ops.render.render(write_still = True)
        
        return {'FINISHED'}


classes = [
    DiscoProps,
    DISCO_PT_main_panel, 
    AddColorMaterialOperator, 
    AddRandomMaterialOperator, 
    Generate5x5Operator, 
    DeleteAllObjectsOperator,
    PrekeyOperator]
 
 
 
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