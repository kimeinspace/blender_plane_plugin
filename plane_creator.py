bl_info = {
    "name": "参数化平面创建器",
    "author": "BIG_D",
    "version": (2, 2),
    "blender": (3, 0, 0),
    "location": "View3D > Add > Mesh > 指定尺寸平面",
    "description": "弹出对话框创建平面，支持单位选择（mm/cm/m/inch/ft）",
    "category": "Add Mesh",
}

import bpy
from bpy.props import FloatProperty, EnumProperty
from mathutils import Vector

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

# ========== 切换单位 ==========
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

# ========== 平面原点对齐 ==========
    origin_mode: EnumProperty(
        name="游标对齐方式",
        description="选择游标对应平面的哪个位置",
        items=[
            ('CENTER', "游标中心", "平面中心对齐游标"),
            ('TOP_LEFT', "游标左上角", "平面的左上角对齐游标"),
        ],
        default='CENTER',
    )

# ========== 线段原点对齐 ==========
    curve_origin_mode: EnumProperty(
            name="样条线游标对齐方式",
            description="选择游标对应样条线的哪个位置",
            items=[
                ('CENTER', "游标中心", "样条线中心对齐游标"),
                ('LEFT', "游标左端", "样条线左端点对齐游标"),
            ],
            default='CENTER',
        )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "unit")
        layout.prop(self, "origin_mode")
        layout.prop(self, "curve_origin_mode")
        
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

        # 获取当前 3D 游标的位置
        cursor_loc = context.scene.cursor.location

        if prefs.origin_mode == 'CENTER':
            plane_center = cursor_loc
        else:  # TOP_LEFT
            # 假设平面的左上角是：X 最小（左），Y 最大（上）
            # 平面中心需要向右偏移 half_length，向下偏移 half_width
            offset_x = length_m / 2
            offset_y = width_m / 2
            plane_center = cursor_loc + Vector((offset_x, offset_y, 0))

        # 创建平面，位置放在游标处
        bpy.ops.mesh.primitive_plane_add(
            size=2,
            enter_editmode=False,
            align='WORLD',
            location=plane_center,
            scale=(1, 1, 1)
        )

        obj = context.active_object
        if obj and obj.type == 'MESH':
            obj.dimensions = (length_m, width_m, 0)
            self.report({'INFO'}, f"已创建平面: {self.length:.2f}{unit} → {length_m:.3f}m × {width_m:.3f}m，模式: {'中心' if prefs.origin_mode=='CENTER' else '左上角'}")
        else:
            self.report({'ERROR'}, "创建失败")
            return {'CANCELLED'}

        return {'FINISHED'}

    def invoke(self, context, event):
        # 弹出对话框，让用户输入长和宽
        return context.window_manager.invoke_props_dialog(self, width=300)

class CURVE_OT_add_line_by_length(bpy.types.Operator):
    bl_idname = "curve.add_line_by_length"
    bl_label = "创建指定长度样条线"
    bl_options = {'REGISTER', 'UNDO'}

    length: FloatProperty(
        name="长度",
        description="样条线的长度",
        default=1000.0,
        min=0.01,
    )

    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        unit = prefs.unit
        scale = UNIT_TO_METER[unit]
        length_m = self.length * scale

        cursor_loc = context.scene.cursor.location
        mode = prefs.curve_origin_mode

        # 计算起点和终点（沿 X 轴方向）
        if mode == 'CENTER':
            start = cursor_loc - Vector((length_m / 2, 0, 0))
            end   = cursor_loc + Vector((length_m / 2, 0, 0))
        else:  # LEFT
            start = cursor_loc
            end   = cursor_loc + Vector((length_m, 0, 0))

        # 创建曲线数据
        curve_data = bpy.data.curves.new(name="Line", type='CURVE')
        curve_data.dimensions = '3D'
        spline = curve_data.splines.new('POLY')
        spline.points.add(1)
        spline.points[0].co = (start.x, start.y, start.z, 1)
        spline.points[1].co = (end.x,   end.y,   end.z,   1)

        # 创建曲线对象并链接到场景
        curve_obj = bpy.data.objects.new("Line", curve_data)
        context.collection.objects.link(curve_obj)
        # 将新对象设为活动对象并选中
        bpy.context.view_layer.objects.active = curve_obj
        curve_obj.select_set(True)

        self.report({'INFO'}, f"已创建样条线: {self.length:.2f}{unit} → {length_m:.3f}m，模式: {'中心' if mode=='CENTER' else '左端'}")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)

# -------------------------------------------------------------------
# 菜单项（添加到 Add > Mesh）
# -------------------------------------------------------------------
def menu_func_plane(self, context):
    self.layout.operator(MESH_OT_add_plane_by_dimensions.bl_idname,
                         text="指定尺寸平面",
                         icon='MESH_PLANE')

def menu_func_curve(self, context):
    self.layout.operator(CURVE_OT_add_line_by_length.bl_idname,
                         text="指定长度样条线",
                         icon='CURVE_DATA')

# -------------------------------------------------------------------
# 注册与注销
# -------------------------------------------------------------------
classes = [PlaneCreatorPreferences, MESH_OT_add_plane_by_dimensions, CURVE_OT_add_line_by_length]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func_plane)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func_curve)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func_plane)
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func_curve)

if __name__ == "__main__":
    register()
