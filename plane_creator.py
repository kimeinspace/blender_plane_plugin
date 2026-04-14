bl_info = {
    "name": "参数化平面创建器",
    "author": "BIG_D",
    "version": (2, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Add > Mesh > 指定尺寸平面",
    "description": "弹出对话框创建平面，支持单位选择（mm/cm/m/inch/ft）",
    "category": "Add Mesh",
}

import bpy
from bpy.props import FloatProperty, EnumProperty

# -------------------------------------------------------------------
# 单位转换表（转成米）
# -------------------------------------------------------------------
UNIT_TO_METER = {
    'mm': 0.001,
    'cm': 0.01,
    'm': 1.0,
    'inch': 0.0254,
    'ft': 0.3048,
}

# -------------------------------------------------------------------
# 插件偏好设置（用户可在 Blender 偏好中修改单位）
# -------------------------------------------------------------------
class PlaneCreatorPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    unit: EnumProperty(
        name="输入单位",
        description="创建平面时，你输入的尺寸所使用的单位",
        items=[
            ('mm', "毫米", "毫米 (mm)"),
            ('cm', "厘米", "厘米 (cm)"),
            ('m', "米", "米 (m)"),
            ('inch', "英寸", "英寸 (inch)"),
            ('ft', "英尺", "英尺 (ft)"),
        ],
        default='mm',
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "unit")

# -------------------------------------------------------------------
# 创建平面的 Operator（带对话框）
# -------------------------------------------------------------------
class MESH_OT_add_plane_by_dimensions(bpy.types.Operator):
    bl_idname = "mesh.add_plane_by_dimensions"
    bl_label = "创建指定尺寸平面"
    bl_options = {'REGISTER', 'UNDO'}

    length: FloatProperty(
        name="长度 (X)",
        description="平面的长度",
        default=1000.0,
        min=0.01,
    )
    width: FloatProperty(
        name="宽度 (Y)",
        description="平面的宽度",
        default=1000.0,
        min=0.01,
    )

    def execute(self, context):
        # 获取插件偏好中的单位设置
        prefs = context.preferences.addons[__name__].preferences
        unit = prefs.unit
        scale = UNIT_TO_METER[unit]

        # 将用户输入的数值转换为米
        length_m = self.length * scale
        width_m = self.width * scale

        # 创建平面（默认边长 2 米，再缩放至目标尺寸）
        bpy.ops.mesh.primitive_plane_add(
            size=2,
            enter_editmode=False,
            align='WORLD',
            location=(0, 0, 0),
            scale=(1, 1, 1)
        )

        obj = context.active_object
        if obj and obj.type == 'MESH':
            obj.dimensions = (length_m, width_m, 0)
            self.report({'INFO'}, f"已创建平面: {self.length:.2f}{unit} → {length_m:.3f}m × {width_m:.3f}m")
        else:
            self.report({'ERROR'}, "创建失败")
            return {'CANCELLED'}

        return {'FINISHED'}

    def invoke(self, context, event):
        # 弹出对话框，让用户输入长和宽
        return context.window_manager.invoke_props_dialog(self, width=300)

# -------------------------------------------------------------------
# 菜单项（添加到 Add > Mesh）
# -------------------------------------------------------------------
def menu_func(self, context):
    self.layout.operator(MESH_OT_add_plane_by_dimensions.bl_idname,
                         text="指定尺寸平面",
                         icon='MESH_PLANE')

# -------------------------------------------------------------------
# 注册与注销
# -------------------------------------------------------------------
classes = [PlaneCreatorPreferences, MESH_OT_add_plane_by_dimensions]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()
