import bpy
#context = bpy.context
#obj = context.object

namelist = [
    ["spine01","spine_01"], 
    ["spine02","spine_02"],
    ["spine03","spine_03"],
    ["neck","neck_01"],
    ["upperarm_twist_L","upperarm_twist_01_l"],
    ["upperarm_twist_R","upperarm_twist_01_r"],
    ["lowerarm_twist_L","lowerarm_twist_01_l"],
    ["lowerarm_twist_R","lowerarm_twist_01_r"],
    ["thumb01_L","thumb_01_l"],
    ["thumb02_L","thumb_02_l"],
    ["thumb03_L","thumb_03_l"],
    ["thumb01_R","thumb_01_r"],
    ["thumb02_R","thumb_02_r"],
    ["thumb03_R","thumb_03_r"],
    ["index01_L","index_01_l"],
    ["index02_L","index_02_l"],
    ["index03_L","index_03_l"],
    ["index01_R","index_01_r"],
    ["index02_R","index_02_r"],
    ["index03_R","index_03_r"],
    ["middle01_L","middle_01_l"],
    ["middle02_L","middle_02_l"],
    ["middle03_L","middle_03_l"],
    ["middle01_R","middle_01_r"],
    ["middle02_R","middle_02_r"],
    ["middle03_R","middle_03_r"],
    ["ring01_L","ring_01_l"],
    ["ring02_L","ring_02_l"],
    ["ring03_L","ring_03_l"],
    ["ring01_R","ring_01_r"],
    ["ring02_R","ring_02_r"],
    ["ring03_R","ring_03_r"],
    ["pinky01_L","pinky_01_l"],
    ["pinky02_L","pinky_02_l"],
    ["pinky03_L","pinky_03_l"],
    ["pinky01_R","pinky_01_r"],
    ["pinky02_R","pinky_02_r"],
    ["pinky03_R","pinky_03_r"],
    ["thigh_twist_L","thigh_twist_01_l"],
    ["thigh_twist_R","thigh_twist_01_r"],
    ["calf_twist_L","calf_twist_01_l"],
    ["calf_twist_R","calf_twist_01_r"],
    ["toes_L","ball_l"],
    ["toes_R","ball_r"]
]

for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        obj.name = "Armature"
        for name, newname in namelist:
            # get the pose bone with name
            pb = obj.pose.bones.get(name)
            # continue if no bone of that name
            if pb is None:
                continue
            # rename
            pb.name = newname
        break