import bpy
import numpy as np
import json
import phobos
from phobos.blender.operators.io import createRobot
from phobos.blender.utils import blender as bUtils
from phobos.blender.utils import selection as sUtils
from phobos.blender.model import poses
import logging

ROBOT_NAME = "shadowhand"

def set_pose(modelname: str, p: list, r: list, pose_dict: dict, rotation_mode="XYZ", ignore_limits=False, keyframe=None):
    root = sUtils.getModelRoot(modelname)
    if not root:
        logging.error(f"No model found with the name {modelname}")
        return
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    # Unhide all links from viewport
    
    # bpy.ops.object.select_all(action='SELECT')
    links = sUtils.getChildren(root, ('link',), False, True)
    print(links)  
    sUtils.selectObjects([root] + links, clear=True, active=0)
    bpy.ops.object.mode_set(mode='POSE')
    for link in (link for link in links if 'joint/type' in link and link['joint/type'] not in ['fixed', 'floating']):
        j_value = pose_dict[link["joint/name"]]
        j_value = j_value if not ignore_limits else np.clip(j_value, link["joint/limits/lower"], link["joint/limits/upper"])
        if link["joint/type"] == "prismatic":
            link.pose.bones['Bone'].location.y = j_value
            if isinstance(keyframe, int) and keyframe > 0:
                link.pose.bones['Bone'].keyframe_insert(data_path='location', frame=keyframe)
        else:
            link.pose.bones['Bone'].rotation_mode = "XYZ"
            link.pose.bones['Bone'].rotation_euler.y = j_value
            if isinstance(keyframe, int) and keyframe > 0:
                link.pose.bones['Bone'].keyframe_insert(data_path='rotation_euler', frame=keyframe)
            
    bpy.ops.object.mode_set(mode='OBJECT')
    # set root pose
    root.location = p
    root.rotation_mode = rotation_mode
    root.rotation_euler = r
    if isinstance(keyframe, int) and keyframe > 0:
        root.keyframe_insert(data_path='location', frame=keyframe)
        root.keyframe_insert(data_path='rotation_euler', frame=keyframe)
    
# Creating robots from the given API has bugs. Use the template .blend file instead.
# robot = phobos.core.Robot(inputfile="data/urdf/shadow_hand_description/shadowhand.urdf")
# createRobot(robot)

traj_data = json.load(open("data/demo_trajectory.json", 'r'))
joint_names = traj_data["joint_names"]
rotation_mode = traj_data["rotation_mode"]

for t, frame in enumerate(traj_data["trajectory"]):
    p, r, q = frame["p"], frame["r"], frame["q"]
    pose_dict = dict(zip(joint_names, q))
    set_pose(ROBOT_NAME, p, r, pose_dict, rotation_mode, ignore_limits=False, keyframe=t * 12)
    