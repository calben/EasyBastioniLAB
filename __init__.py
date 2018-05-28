#ManuelbastioniLAB - Copyright (C) 2015-2018 Manuel Bastioni
#Official site: www.manuelbastioni.com
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.


bl_info = {
    "name": "EasyBastioniLAB",
    "author": "iGotcha Media, Manuel Bastioni",
    "version": (1, 6, 1),
    "blender": (2, 7, 9),
    "location": "View3D > Tools > EasyBastioniLAB",
    "description": "An easy lab for character creation",
    "warning": "",
    'wiki_url': "http://www.manuelbastioni.com",
    "category": "Characters"}

import bpy
import os
import json
from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.app.handlers import persistent
from . import humanoid, animationengine, proxyengine
import time
import logging

#new imports - EasyBastioniLAB
import bpy.utils.previews
import bpy_extras
import mathutils
from math import radians
from subprocess import call
import uuid
import re
import subprocess
from bpy.props import EnumProperty

#import cProfile, pstats, io
#import faulthandler
#faulthandler.enable()

log_path = os.path.join(bpy.context.user_preferences.filepaths.temporary_directory, "manuellab_log.txt")
log_is_writeable = True

try:
    test_writing = open(log_path, 'w')
    test_writing.close()
except:
    print("WARNING: Writing permission error for {0}".format(log_path))
    print("The log will be redirected to the console (here)")
    log_is_writeable = False

lab_logger = logging.getLogger('manuelbastionilab_logger')
lab_logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

if log_is_writeable:

    fhandler = logging.FileHandler(log_path, mode ='w')
    fhandler.setLevel(logging.INFO)
    chandler = logging.StreamHandler()
    chandler.setLevel(logging.WARNING)
    fhandler.setFormatter(formatter)
    chandler.setFormatter(formatter)
    lab_logger.addHandler(fhandler)
    lab_logger.addHandler(chandler)

else:

    chandler = logging.StreamHandler()
    chandler.setLevel(logging.INFO)
    chandler.setFormatter(formatter)
    lab_logger.addHandler(chandler)

mblab_humanoid = humanoid.Humanoid(bl_info["version"])
mblab_retarget = animationengine.RetargetEngine()
mblab_shapekeys = animationengine.ExpressionEngineShapeK()
mblab_proxy = proxyengine.ProxyEngine()

#wellvr global variables
advanced_mode_is_on = False
viewOnBody = 0

gui_status = "NEW_SESSION"
gui_err_msg = ""
gui_active_panel = None
gui_active_panel_fin = None

def start_lab_session():

    global mblab_humanoid
    global gui_status,gui_err_msg

    lab_logger.info("Start_the lab session...")
    scn = bpy.context.scene
    character_identifier = scn.mblab_character_name
    rigging_type = "base"
    if scn.mblab_use_ik:
        rigging_type = "ik"
    if scn.mblab_use_muscle:
        rigging_type = "muscle"
    if scn.mblab_use_muscle and scn.mblab_use_ik:
        rigging_type = "muscle_ik"

    lib_filepath = algorithms.get_blendlibrary_path()

    obj = None
    is_existing = False
    is_obj = algorithms.looking_for_humanoid_obj()


    if is_obj[0] == "ERROR":
        gui_status = "ERROR_SESSION"
        gui_err_msg = is_obj[1]
        return

    if is_obj[0] == "NO_OBJ":
        base_model_name = mblab_humanoid.characters_config[character_identifier]["template_model"]
        obj = algorithms.import_object_from_lib(lib_filepath, base_model_name, character_identifier)
        obj["manuellab_vers"] = bl_info["version"]
        obj["manuellab_id"] = character_identifier
        obj["manuellab_rig"] = rigging_type

    if is_obj[0] == "FOUND":
        obj = algorithms.get_object_by_name(is_obj[1])
        character_identifier = obj["manuellab_id"]
        rigging_type = obj["manuellab_rig"]
        is_existing = True

    if not obj:
        lab_logger.critical("Init failed. Check the log file: {0}".format(log_path))
        gui_status = "ERROR_SESSION"
        gui_err_msg = "Init failed. Check the log file"
    else:
        mblab_humanoid.init_database(obj,character_identifier,rigging_type)
        if mblab_humanoid.has_data:
            gui_status = "ACTIVE_SESSION"

            if scn.mblab_use_cycles:
                scn.render.engine = 'CYCLES'
                if scn.mblab_use_lamps:
                    algorithms.import_object_from_lib(lib_filepath, "Lamp_back_bottom")
                    algorithms.import_object_from_lib(lib_filepath, "Lamp_back_up")
                    algorithms.import_object_from_lib(lib_filepath, "Lamp_left")
                    algorithms.import_object_from_lib(lib_filepath, "Lamp_right")
                    #algorithms.append_object_from_library(lib_filepath, [], "Lamp_")
            else:
                scn.render.engine = 'BLENDER_RENDER'



            lab_logger.info("Rendering engine now is {0}".format(scn.render.engine))
            init_morphing_props(mblab_humanoid)
            init_categories_props(mblab_humanoid)
            init_measures_props(mblab_humanoid)
            init_restposes_props(mblab_humanoid)
            init_presets_props(mblab_humanoid)
            init_ethnic_props(mblab_humanoid)
            init_metaparameters_props(mblab_humanoid)
            init_material_parameters_props(mblab_humanoid)
            mblab_humanoid.update_materials()

            if is_existing:
                lab_logger.info("Re-init the character {0}".format(obj.name))
                mblab_humanoid.store_mesh_in_cache()
                mblab_humanoid.reset_mesh()
                mblab_humanoid.recover_prop_values_from_obj_attr()
                mblab_humanoid.restore_mesh_from_cache()
            else:
                mblab_humanoid.reset_mesh()
                mblab_humanoid.update_character(mode = "update_all")

            algorithms.deselect_all_objects()

            if mblab_humanoid.get_subd_visibility() == True:
                mblab_humanoid.set_subd_visibility(False)
            if mblab_humanoid.get_smooth_visibility() == True:
                mblab_humanoid.set_smooth_visibility(False)

            # Set shader to material
            for area in bpy.context.screen.areas: # iterate through areas in current screen
                if area.type == 'VIEW_3D':
                    for space in area.spaces: # iterate through spaces in current VIEW_3D area
                        if space.type == 'VIEW_3D': # check if space is a 3D view
                            space.viewport_shade = 'MATERIAL' # set the viewport shading to material

            v3d = bpy.context.space_data
            rv3d = v3d.region_3d
            rv3d.view_distance = 2
            rv3d.view_location.z = 1
            eul = mathutils.Euler((radians(75), 0.0, 0.0), 'XYZ')
            rv3d.view_rotation = eul.to_quaternion()



@persistent
def check_manuelbastionilab_session(dummy):
    global mblab_humanoid
    global gui_status, gui_err_msg
    scn = bpy.context.scene
    if mblab_humanoid:
        init_femaleposes_props()
        init_maleposes_props()
        gui_status = "NEW_SESSION"
        is_obj = algorithms.looking_for_humanoid_obj()
        if is_obj[0] == "FOUND":
            #gui_status = "RECOVERY_SESSION"
            #if scn.do_not_ask_again:
            start_lab_session()
        if is_obj[0] == "ERROR":
            gui_status = "ERROR_SESSION"
            gui_err_msg = is_obj[1]
            return

bpy.app.handlers.load_post.append(check_manuelbastionilab_session)


def sync_character_to_props():
    #It's important to avoid problems with Blender undo system
    global mblab_humanoid
    mblab_humanoid.sync_character_data_to_obj_props()
    mblab_humanoid.update_character()

def realtime_update(self, context):
    """
    Update the character while the prop slider moves.
    """
    global mblab_humanoid
    if mblab_humanoid.bodydata_realtime_activated:
        #time1 = time.time()
        scn = bpy.context.scene
        mblab_humanoid.update_character(category_name = scn.morphingCategory, mode="update_realtime")
        mblab_humanoid.sync_gui_according_measures()
        #print("realtime_update: {0}".format(time.time()-time1))

def age_update(self, context):
    global mblab_humanoid
    time1 = time.time()
    if mblab_humanoid.metadata_realtime_activated:
        time1 = time.time()
        mblab_humanoid.calculate_transformation("AGE")

def mass_update(self, context):
    global mblab_humanoid
    if mblab_humanoid.metadata_realtime_activated:
        mblab_humanoid.calculate_transformation("FAT")

def tone_update(self, context):
    global mblab_humanoid
    if mblab_humanoid.metadata_realtime_activated:
        mblab_humanoid.calculate_transformation("MUSCLE")

def modifiers_update(self, context):
    sync_character_to_props()

def dud_modifiers_update(self, context):
    #nothing to see here folks
    print ("potato")


def preset_update(self, context):
    """
    Update the character while prop slider moves
    """
    scn = bpy.context.scene
    global mblab_humanoid
    obj = mblab_humanoid.get_object()
    filepath = os.path.join(
        mblab_humanoid.presets_path,
        "".join([obj.preset, ".json"]))
    mblab_humanoid.load_character(filepath, mix=scn.mblab_mix_characters)

def ethnic_update(self, context):
    scn = bpy.context.scene
    global mblab_humanoid
    obj = mblab_humanoid.get_object()
    filepath = os.path.join(
        mblab_humanoid.phenotypes_path,
        "".join([obj.ethnic, ".json"]))
    mblab_humanoid.load_character(filepath, mix=scn.mblab_mix_characters)

def material_update(self, context):
    global mblab_humanoid
    if mblab_humanoid.material_realtime_activated:
        mblab_humanoid.update_materials(update_textures_nodes = False)

def measure_units_update(self, context):
    global mblab_humanoid
    mblab_humanoid.sync_gui_according_measures()

def human_expression_update(self, context):
    global mblab_shapekeys
    scn = bpy.context.scene
    mblab_shapekeys.sync_expression_to_GUI()

def restpose_update(self, context):
    global mblab_humanoid
    armature = mblab_humanoid.get_armature()
    filepath = os.path.join(
        mblab_humanoid.restposes_path,
        "".join([armature.rest_pose, ".json"]))
    mblab_retarget.load_pose(filepath, armature)

def malepose_update(self, context):
    global mblab_retarget
    armature = algorithms.get_active_armature()
    filepath = os.path.join(
        mblab_retarget.maleposes_path,
        "".join([armature.male_pose, ".json"]))
    mblab_retarget.load_pose(filepath, use_retarget = True)

def femalepose_update(self, context):
    global mblab_retarget
    armature = algorithms.get_active_armature()
    filepath = os.path.join(
        mblab_retarget.femaleposes_path,
        "".join([armature.female_pose, ".json"]))
    mblab_retarget.load_pose(filepath, use_retarget = True)


def init_morphing_props(humanoid_instance):
    for prop in humanoid_instance.character_data:
        setattr(
            bpy.types.Object,
            prop,
            bpy.props.FloatProperty(
                name=prop,
                min = -5.0,
                max = 5.0,
                soft_min = 0.0,
                soft_max = 1.0,
                precision=3,
                default=0.5,
                update=None))

def init_measures_props(humanoid_instance):
    for measure_name,measure_val in humanoid_instance.morph_engine.measures.items():
        setattr(
            bpy.types.Object,
            measure_name,
            bpy.props.FloatProperty(
                name=measure_name, min=0.0, max=500.0,
                default=measure_val))
    humanoid_instance.sync_gui_according_measures()


def init_categories_props(humanoid_instance):
    categories_enum = []
    for category in mblab_humanoid.get_categories()  :
        categories_enum.append(
            (category.name, category.name, category.name))

    bpy.types.Scene.morphingCategory = bpy.props.EnumProperty(
        items=categories_enum,
        update = modifiers_update,
        name="Morphing categories")


    # categories_shortlist_enum = []
    # for category in mblab_humanoid.get_categories_shortlist():
    #     categories_shortlist_enum.append((category.name, category.name, category.name))
    #
    # bpy.types.Scene.shortMorphingCategory = bpy.props.EnumProperty(
    #     items=categories_shortlist_enum,
    #     update = dud_modifiers_update,
    #     name="Shortlist morphing categories")

def init_restposes_props(humanoid_instance):
    if humanoid_instance.exists_rest_poses_database():
        restpose_items = algorithms.generate_items_list(humanoid_instance.restposes_path)
        bpy.types.Object.rest_pose = bpy.props.EnumProperty(
            items=restpose_items,
            name="Rest pose",
            default=restpose_items[0][0],
            update=restpose_update)

        for item in restpose_items:
            if (item[0] == 't-pose'):
                wellvr_restpose_update()


def wellvr_restpose_update():
    global mblab_humanoid
    armature = mblab_humanoid.get_armature()
    filepath = os.path.join(
        mblab_humanoid.restposes_path,
        "".join([armature.rest_pose, ".json"]))
    mblab_retarget.load_pose(filepath, armature)

def init_maleposes_props():
    global mblab_retarget
    if mblab_retarget.maleposes_exist:
        malepose_items = algorithms.generate_items_list(mblab_retarget.maleposes_path)
        bpy.types.Object.male_pose = bpy.props.EnumProperty(
            items=malepose_items,
            name="Male pose",
            default=malepose_items[0][0],
            update=malepose_update)

def init_femaleposes_props():
    global mblab_retarget
    if mblab_retarget.femaleposes_exist:
        femalepose_items = algorithms.generate_items_list(mblab_retarget.femaleposes_path)
        bpy.types.Object.female_pose = bpy.props.EnumProperty(
            items=femalepose_items,
            name="Female pose",
            default=femalepose_items[0][0],
            update=femalepose_update)


def init_expression_props():
    for expression_name in mblab_shapekeys.expressions_labels:
        setattr(
            bpy.types.Object,
            expression_name,
            bpy.props.FloatProperty(
                name=expression_name,
                min = 0.0,
                max = 1.0,
                precision=3,
                default=0.0,
                update=human_expression_update))



def init_presets_props(humanoid_instance):
    if humanoid_instance.exists_preset_database():
        preset_items = algorithms.generate_items_list(humanoid_instance.presets_path)
        bpy.types.Object.preset = bpy.props.EnumProperty(
            items=preset_items,
            name="Types",
            update=preset_update)

def init_ethnic_props(humanoid_instance):
    if humanoid_instance.exists_phenotype_database():
        ethnic_items = algorithms.generate_items_list(humanoid_instance.phenotypes_path)
        bpy.types.Object.ethnic = bpy.props.EnumProperty(
            items=ethnic_items,
            name="Phenotype",
            update=ethnic_update)

def init_metaparameters_props(humanoid_instance):
    for meta_data_prop in humanoid_instance.character_metaproperties.keys():
        upd_function = None

        if "age" in meta_data_prop:
            upd_function = age_update
        if "mass" in meta_data_prop:
            upd_function = mass_update
        if "tone" in meta_data_prop:
            upd_function = tone_update
        if "last" in meta_data_prop:
            upd_function = None

        if "last_" not in meta_data_prop:
            setattr(
                bpy.types.Object,
                meta_data_prop,
                bpy.props.FloatProperty(
                    name=meta_data_prop, min=-1.0, max=1.0,
                    precision=3,
                    default=0.0,
                    update=upd_function))


def init_material_parameters_props(humanoid_instance):

    for material_data_prop, value in humanoid_instance.character_material_properties.items():
        setattr(
            bpy.types.Object,
            material_data_prop,
            bpy.props.FloatProperty(
                name=material_data_prop,
                min = 0.0,
                max = 1.0,
                precision=2,
                update = material_update,
                default=value))

def angle_update_0(self, context):
    global mblab_retarget
    scn = bpy.context.scene
    value = scn.mblab_rot_offset_0
    mblab_retarget.correct_bone_angle(0,value)

def angle_update_1(self, context):
    global mblab_retarget
    scn = bpy.context.scene
    value = scn.mblab_rot_offset_1
    mblab_retarget.correct_bone_angle(1,value)


def angle_update_2(self, context):
    global mblab_retarget
    scn = bpy.context.scene
    value = scn.mblab_rot_offset_2
    mblab_retarget.correct_bone_angle(2,value)

def generate_skin_previews():
    pcoll = preview_collections["skin_previews"]
    image_location = pcoll.images_location
    VALID_EXTENSIONS = ('.png', '.jpg', '.jpeg')

    enum_items = []

    # Generate the thumbnails
    for i, image in enumerate(os.listdir(image_location)):
        if image.endswith(VALID_EXTENSIONS):
            filepath = os.path.join(image_location, image)
            thumb = pcoll.load(filepath, filepath, 'IMAGE')
            enum_items.append((image, image, "", thumb.icon_id, i))

    return enum_items

def skin_previews_update(self, context):
    global mblab_humanoid
    # place skin complexion and hue in the .png's name!
    selected_skin_preview_name = bpy.context.scene.skin_previews
    selected_skin_preview_name = selected_skin_preview_name[:(len(selected_skin_preview_name) - 4)]
    split_skin_preview_name = selected_skin_preview_name.split('_')
    for split_value in split_skin_preview_name:
        if 'complexion' in split_value:
            split_complexion = split_value.split('-')
            complexion_value = float(split_complexion[1])
            # complexion_value /= 1000
            mblab_humanoid.character_material_properties['skin_complexion'] = complexion_value
        if 'hue' in split_value:
            split_hue = split_value.split('-')
            hue_value = float(split_hue[1])
            # hue_value /= 1000
            mblab_humanoid.character_material_properties['skin_hue'] = hue_value

    mblab_humanoid.material_realtime_activated = False
    obj = mblab_humanoid.get_object()
    for material_data_prop, value in mblab_humanoid.character_material_properties.items():
        if 'skin_hue' in material_data_prop or 'skin_complexion' in material_data_prop:
            if hasattr(obj, material_data_prop):
                setattr(obj, material_data_prop, value)
            else:
                lab_logger.warning("material {0}  not found".format(material_data_prop))

    mblab_humanoid.material_realtime_activated = True
    mblab_humanoid.update_materials()

def generate_morph_previews(morph_target):
    pcoll = preview_collections[morph_target]
    image_location = pcoll.images_location
    VALID_EXTENSIONS = ('.png', '.jpg', '.jpeg')

    enum_items = []

    images_dir = os.path.join(image_location, morph_target)
    # Generate the thumbnails
    for i, image in enumerate(os.listdir(images_dir)):
        if image.endswith(VALID_EXTENSIONS):
            filepath = os.path.join(images_dir, image)
            thumb = pcoll.load(filepath, filepath, 'IMAGE')
            enum_items.append((image, image, "", thumb.icon_id, i))

    return enum_items

def morph_previews_update(self, context, morph_target):
    global mblab_humanoid

    selected_morph_target_name = getattr(bpy.context.scene, morph_target)
    selected_morph_target_name = selected_morph_target_name[:(len(selected_morph_target_name) - 4)]
    print(selected_morph_target_name)
    split_morph_target_name = selected_morph_target_name.rsplit('_', 1)
    print(split_morph_target_name[-1])
    print(split_morph_target_name[0])
    prop = split_morph_target_name[0]

    mblab_humanoid.character_data[prop] = float(split_morph_target_name[-1])
    print(mblab_humanoid.character_data[prop])
    if mblab_humanoid.character_data[prop] > 1:
        mblab_humanoid.character_data[prop] = 1
    elif mblab_humanoid.character_data[prop] < 0:
        mblab_humanoid.character_data[prop] = 0
    scn = bpy.context.scene
    # maybe not use update_all here? Try update_only_morphdata, or update_directly_verts
    mblab_humanoid.update_character(category_name = scn.morphingCategory, mode="update_all")
    # print("Got", mblab_humanoid.character_data[prop])

def morph_previews_update_closure(morph_target):
    return lambda a,b: morph_previews_update(a,b,morph_target)


def save_metadata_json(filepath):

    dir_path = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    filename_root = os.path.splitext(filename)[0]
    new_filename = filename_root + '_metadata.json'
    new_filepath = os.path.join(dir_path,new_filename)

    scene = bpy.context.scene
    if "f_" in scene.mblab_character_name:
        char_gender = "female"
    elif "m_" in scene.mblab_character_name:
        char_gender = "male"
    else:
        char_gender = "non-binary"

    obj = mblab_humanoid.get_object()
    char_ethnic_group = obj.ethnic
    char_body_preset = obj.preset

    char_data = {"manuellab_vers": mblab_humanoid.lab_vers, "gender": char_gender, "ethnic_group": char_ethnic_group, "body_preset": char_body_preset}

    output_file = open(new_filepath, 'w')
    json.dump(char_data, output_file)
    output_file.close()

init_expression_props()

bpy.types.Scene.mblab_final_prefix = bpy.props.StringProperty(
        name="Prefix",
        description="The prefix of names for finalized model, skeleton and materials. If none, it will be generated automatically" ,
        default="")

bpy.types.Scene.mblab_rot_offset_0 = bpy.props.FloatProperty(
        name="Tweak rot X",
        min = -1,
        max = 1,
        precision=2,
        update = angle_update_0,
        default=0.0)

bpy.types.Scene.mblab_rot_offset_1 = bpy.props.FloatProperty(
        name="Tweak rot Y",
        min = -1,
        max = 1,
        precision=2,
        update = angle_update_1,
        default=0.0)

bpy.types.Scene.mblab_rot_offset_2 = bpy.props.FloatProperty(
        name="Tweak rot Z",
        min = -1,
        max = 1,
        precision=2,
        update = angle_update_2,
        default=0.0)

bpy.types.Scene.mblab_proxy_offset = bpy.props.FloatProperty(
        name="Offset",
        min = 0,
        max = 100,
        default=0)

bpy.types.Scene.mblab_proxy_threshold = bpy.props.FloatProperty(
        name="Influence",
        min = 0,
        max = 1000,
        default=500)

bpy.types.Scene.mblab_use_ik = bpy.props.BoolProperty(
    name="Use Inverse Kinematic",
    default = False,
    description="Use inverse kinematic armature")

bpy.types.Scene.mblab_use_muscle = bpy.props.BoolProperty(
    name="Use basic muscles",
    default = False,
    description="Use basic muscle armature")

bpy.types.Scene.mblab_remove_all_modifiers = bpy.props.BoolProperty(
    name="Remove modifiers",
    default = False,
    description="If checked, all the modifiers will be removed, except the armature one (displacement, subdivision, corrective smooth, etc) will be removed from the finalized character)")

bpy.types.Scene.mblab_use_cycles = bpy.props.BoolProperty(
    name="Use Cycles materials (needed for skin shaders)",
    default = True,
    description="This is needed in order to use the skin editor and shaders (highly recommended)")

bpy.types.Scene.mblab_use_lamps = bpy.props.BoolProperty(
    name="Use portrait studio lights (recommended)",
    default = False,
    description="Add a set of lights optimized for portrait. Useful during the design of skin (recommended)")

bpy.types.Scene.mblab_show_measures = bpy.props.BoolProperty(
    name="Body measures",
    description="Show measures controls",
    update = modifiers_update)

bpy.types.Scene.mblab_measure_filter = bpy.props.StringProperty(
    name="Filter",
    default = "",
    description="Filter the measures to show")

bpy.types.Scene.mblab_expression_filter = bpy.props.StringProperty(
    name="Filter",
    default = "",
    description="Filter the expressions to show")

bpy.types.Scene.mblab_mix_characters = bpy.props.BoolProperty(
    name="Mix with current",
    description="Mix templates")

bpy.types.Scene.mblab_template_name = bpy.props.EnumProperty(
    items=mblab_humanoid.template_types,
    name="Select",
    default="human_female_base")

bpy.types.Scene.mblab_character_name = bpy.props.EnumProperty(
    items=mblab_humanoid.humanoid_types,
    name="Select",
    default="f_ca01")

bpy.types.Scene.mblab_assets_models = bpy.props.EnumProperty(
    items=mblab_proxy.assets_models,
    name="Assets library")

# bpy.types.Scene.mblab_transfer_weights = bpy.props.BoolProperty(
    # name="Transfer rigging",
    # description="Transfers the weights from the body to fitted element, adding an armature modifier",
    # default = True)

# bpy.types.Scene.mblab_overwrite_weights = bpy.props.BoolProperty(
    # name="Replace existing weights",
    # description="If the element has already rigging weights, they will be replaced with the weights projected from the character body",
    # default = False)

bpy.types.Scene.mblab_overwrite_proxy_weights = bpy.props.BoolProperty(
    name="Replace existing proxy weights",
    description="If the proxy has already rigging weights, they will be replaced with the weights projected from the character body",
    default = False)

bpy.types.Scene.mblab_save_images_and_backup = bpy.props.BoolProperty(
    name="Save images and backup character",
    description="Save all images from the skin shader and backup the character in json format",
    default = True)

bpy.types.Object.mblab_use_inch = bpy.props.BoolProperty(
    name="Inch",
    update = measure_units_update,
    description="Use inch instead of cm")

bpy.types.Scene.mblab_export_proportions = bpy.props.BoolProperty(
    name="Include proportions",
    description="Include proportions in the exported character file")

bpy.types.Scene.mblab_export_materials = bpy.props.BoolProperty(
    name="Include materials",
    default = True,
    description="Include materials in the exported character file")

bpy.types.Scene.mblab_show_texture_load_save = bpy.props.BoolProperty(
    name="Import-export images",
    description="Show controls to import and export texture images")

bpy.types.Scene.mblab_add_mask_group = bpy.props.BoolProperty(
    name="Add mask vertgroup",
    description="Create a new vertgroup and use it as mask the body under proxy.",
    default=False)

bpy.types.Scene.mblab_preserve_mass = bpy.props.BoolProperty(
    name="Mass",
    description="Preserve the current relative mass percentage")

bpy.types.Scene.mblab_preserve_height = bpy.props.BoolProperty(
    name="Height",
    description="Preserve the current character height")

bpy.types.Scene.mblab_preserve_tone = bpy.props.BoolProperty(
    name="Tone",
    description="Preserve the current relative tone percentage")

bpy.types.Scene.mblab_preserve_fantasy = bpy.props.BoolProperty(
    name="Fantasy",
    description="Preserve the current amount of fantasy morphs. For example, starting from a character with zero fantasy elements, all the generated characters will have zero fantasy elements")

bpy.types.Scene.mblab_preserve_body = bpy.props.BoolProperty(
    name="Body",
    description="Preserve the body features")

bpy.types.Scene.mblab_preserve_face = bpy.props.BoolProperty(
    name="Face",
    description="Preserve the face features, but not the head shape")

bpy.types.Scene.mblab_preserve_phenotype = bpy.props.BoolProperty(
    name="Phenotype",
    description="Preserve characteristic traits, like people that are members of the same family")

bpy.types.Scene.mblab_set_tone_and_mass = bpy.props.BoolProperty(
    name="Use fixed tone and mass values",
    description="Enable the setting of fixed values for mass and tone using a slider UI")

bpy.types.Scene.mblab_body_mass = bpy.props.FloatProperty(
    name="Body mass",
    min=0.0,
    max=1.0,
    default = 0.5,
    description="Preserve the current character body mass")

bpy.types.Scene.mblab_body_tone = bpy.props.FloatProperty(
    name="Body tone",
    min=0.0,
    max=1.0,
    default = 0.5,
    description="Preserve the current character body mass")

bpy.types.Scene.mblab_random_engine = bpy.props.EnumProperty(
                items = [("LI", "Light", "Little variations from the standard"),
                        ("RE", "Realistic", "Realistic characters"),
                        ("NO", "Noticeable", "Very characterized people"),
                        ("CA", "Caricature", "Engine for caricatures"),
                        ("EX", "Extreme", "Extreme characters")],
                name = "Engine",
                default = "LI")

class GenericMorphButtonMinus(bpy.types.Operator):
    bl_idname = "wellvr.generic_morph_button_minus"
    bl_label = "Generic Morph Button Minus"

    morphtargetprop = bpy.props.StringProperty()

    def execute(self, context):
        global mblab_humanoid
        # print("Pressed button", self.morphtargetprop, "min")
        prop = self.morphtargetprop
        print(prop)
        print(mblab_humanoid.character_data[prop])
        mblab_humanoid.character_data[prop] = mblab_humanoid.character_data[prop] - 0.1
        if mblab_humanoid.character_data[prop] > 1:
            mblab_humanoid.character_data[prop] = 1
        elif mblab_humanoid.character_data[prop] < 0:
            mblab_humanoid.character_data[prop] = 0
        scn = bpy.context.scene
        # maybe not use update_all here? Try update_only_morphdata, or update_directly_verts
        mblab_humanoid.update_character(category_name = scn.morphingCategory, mode="update_all")
        # print("Got", mblab_humanoid.character_data[prop])
        return {'FINISHED'}

class GenericMorphButtonPlus(bpy.types.Operator):
    bl_idname = "wellvr.generic_morph_button_plus"
    bl_label = "Generic Morph Button Plus"

    morphtargetprop = bpy.props.StringProperty()

    def execute(self, context):
        global mblab_humanoid
        # print("Pressed button", self.morphtargetprop, "max")
        prop = self.morphtargetprop
        mblab_humanoid.character_data[prop] = mblab_humanoid.character_data[prop] + 0.1
        if mblab_humanoid.character_data[prop] > 1:
            mblab_humanoid.character_data[prop] = 1
        elif mblab_humanoid.character_data[prop] < 0:
            mblab_humanoid.character_data[prop] = 0
        scn = bpy.context.scene
        # maybe not use update_all here? Try update_only_morphdata, or update_directly_verts
        mblab_humanoid.update_character(category_name = scn.morphingCategory, mode="update_all")
        # print("Got", mblab_humanoid.character_data[prop])
        return {'FINISHED'}

class ExportToUnrealButton(bpy.types.Operator):
    bl_idname = "wellvr.export_to_unreal"
    bl_label = "Export To Unreal"

    def execute(self, context):
        global mblab_humanoid
        global gui_status

        # cmd = 'echo $HOME'
        # print (subprocess.check_output(cmd, shell=True))
        # subprocess.call('echo', shell=True)
        # return {'FINISHED'}
        # Get filename from user input. If empty or containing non-alphanumerical letters or underscores, don't export
        # filename = str(uuid.uuid4())
        filename = context.scene.name_input_prop
        if (filename == ''):
            self.report({'INFO'}, "Please enter a name for the character")
            return {'CANCELLED'}
        ex = filename.rstrip()
        if (not re.match(r'^[a-zA-Z0-9][ A-Za-z0-9_-]*$', ex)):
            self.report({'INFO'}, "Alphanumeric characters and underscores only")
            return {'CANCELLED'}

        basedir = os.path.join(os.path.dirname(__file__), "exports/" + context.scene.name_input_prop)
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        # basedir = os.path.dirname(bpy.data.filepath)
        if not basedir:
            raise Exception("Blend file is not saved")

        png_filename = filename + ".png"
        png_basedir = os.path.join(basedir, png_filename)

        scn = bpy.context.scene

        # mblab_humanoid.correct_expressions(correct_all=True)
        # mblab_humanoid.set_rest_pose()
        # mblab_humanoid.remove_modifiers()
        # mblab_humanoid.sync_internal_data_with_mesh()
        # mblab_humanoid.update_displacement()
        # mblab_humanoid.update_materials()
        # mblab_humanoid.save_backup_character(png_basedir)
        # save_metadata_json(png_basedir)
        # mblab_humanoid.save_all_textures(png_basedir)
        #
        # mblab_humanoid.morph_engine.convert_all_to_blshapekeys()
        # mblab_humanoid.delete_all_properties()
        # mblab_humanoid.rename_materials(scn.mblab_final_prefix)
        # mblab_humanoid.update_bendy_muscles()
        # mblab_humanoid.rename_obj(scn.mblab_final_prefix)
        # mblab_humanoid.rename_armature(scn.mblab_final_prefix)

        bpy.context.area.spaces[0].pivot_point='CURSOR'
        bpy.context.area.spaces[0].cursor_location = (0.0, 0.0, 0.0)
        print(bpy.ops.object.mode)
        if (bpy.ops.object.mode != 'OBJECT'):
            bpy.ops.object.mode_set(mode='OBJECT')

        # Load and run attached "bone_rename_script.py" script
        text = bpy.data.texts.load(os.path.join(os.path.dirname(__file__), "bone_rename_script.py"))   # if from disk
        ctx = bpy.context.copy()
        ctx['edit_text'] = text
        bpy.ops.text.run_script(ctx)
        print("Ran bone_rename_script")

        #Transform and save
        scn.unit_settings.system = 'METRIC'
        scn.unit_settings.scale_length = 0.01
        k = 100 #scale constant
        for ob in bpy.data.objects:
            ob.select = True

        bpy.ops.transform.resize(value=(k,k,k))
        bpy.ops.object.transform_apply(scale=True)
        # bpy.ops.wm.save_mainfile()

        bl_region_type = "UI"

        for object in bpy.data.objects:
            if (object.type == "MESH"):
                if (len(list(filter(lambda x : "mbastlab_proxyfit" in x.name, object.data.shape_keys.key_blocks))) > 0):
                    print("Deleting proxy fitting keys from", object.name)
                    object.select = True
                    bpy.context.scene.objects.active = object
                    def del_shape_key(name):
                        i = object.data.shape_keys.key_blocks.keys().index(name)
                        object.active_shape_key_index = i
                        bpy.ops.object.shape_key_remove()
                    del_shape_key("Basis")
                    del_shape_key("mbastlab_proxyfit")

        # mblab_humanoid.remove_modifiers()
        #
        # mblab_humanoid.sync_internal_data_with_mesh()
        # mblab_humanoid.update_displacement()
        # mblab_humanoid.update_materials()
        for object in bpy.data.objects:
            bpy.ops.object.select_all(action='DESELECT')
            object.select = True
            if (object.find_armature() != None):
                object.find_armature().select = True
            export_name = object.name
            if ("MBlab_bd" in object.name):
                export_name = filename
            fn = os.path.join(basedir, export_name)
            print("exporting",object.name)
            print({o.name : o.select for o in bpy.data.objects})
            bpy.ops.export_scene.fbx(filepath=fn + ".fbx", check_existing=True, axis_up='Y', axis_forward='-Z', filter_glob="*.fbx", version='BIN7400', use_selection=True, global_scale=1.0, bake_space_transform=False, object_types={'MESH', 'ARMATURE'}, use_mesh_modifiers=False, mesh_smooth_type='OFF', use_mesh_edges=False, use_tspace=False, use_custom_props=False, add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X', use_armature_deform_only=False, bake_anim=True, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=True, bake_anim_use_all_actions=True, bake_anim_step=1.0, bake_anim_simplify_factor=1.0, use_anim=True, use_anim_action_all=True, use_default_take=True, use_anim_optimize=True, anim_optimize_precision=6.0, path_mode='AUTO', embed_textures=False, batch_mode='OFF', use_batch_own_dir=True, use_metadata=True)
            # bpy.ops.export_scene.fbx(filepath=fn + ".fbx", global_scale=1.0, object_types={'ARMATURE', 'MESH'}, use_mesh_modifiers=False, add_leaf_bones=False)

        print("written:", fn)

        # Set scene back to normal
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        scn.unit_settings.scale_length = 1
        gui_status = "NEW_SESSION"
        # prepare_character_package_arguments = ' '.join(["-p", "\"D:/WellVr/UnrealModPackagerProject/\"",
        #     "-r", "ModPackager.uproject",
        #     "-u", "\"D:/Program Files/Epic Games/UE_4.19/\"",
        #     "-c", filename,
        #     "-d", "\"D:/WellVr/Blender/blender-2.79-windows64/2.79/scripts/addons/easy_bastioni_lab/exports/\"",
        #     "-e", "\"This is not bob.\"",
        #     "-s", "\"Skeleton'/BastioniLABCharacters/Meshes/Male_Caucasian_Athletic_Skeleton.Male_Caucasian_Athletic_Skeleton'",
        #     "-b"])
        call(["S:/WellVrRoot/CharacterPluginGenerator/CreatePluginFromTemplate.Automation/bin/Debug/CreatePluginFromTemplate.Automation.exe",
            "-p", "S:/WellVrRoot/UnrealModPackagerProject/",
            "-r", "ModPackager.uproject",
            "-u", "C:/EpicGamesLibrary/UE_4.19/",
            "-c", filename,
            "-d", "S:/WellVrRoot/CharacterCreator/blender-2.79-windows64/2.79/scripts/addons/easy_bastioni_lab/exports/",
            "-e", "This is not bob.",
            "-s", "Skeleton'/BastioniLABCharacters/Meshes/BaseBastioniCharacter/BaseBastioniCharacter_Skeleton.BaseBastioniCharacter_Skeleton'",
            "-o", "S:/WellVrRoot/CharacterPackages/",
            "-b"], shell=True)
        return {'FINISHED'}

class ExportCharacterPresetsButton(bpy.types.Operator):
    bl_idname = "wellvr.export_character_presets_button"
    bl_label = "Export Character Presets"

    def execute(self, context):
        print("I'm a beautiful toad princess")

        scn = bpy.context.scene
        for character in mblab_humanoid.humanoid_types:
            # print(character[0])
            # if ("Male" in character[0]):
                # print("Got male")
            if not any (value in character[1] for value in ("anime", "elf", "dwarf", "Anime")):
                scn.mblab_character_name = character[0]
                print(character)
                bpy.ops.mbast.init_character('INVOKE_DEFAULT')
                # if mblab_humanoid.exists_phenotype_database():
                    # ethnic_items = algorithms.generate_items_list(mblab_humanoid.phenotypes_path)
                    # for phenotype in ethnic_items:
                    #     obj = mblab_humanoid.get_object()
                    #     obj.ethnic = phenotype[0]
                    #     filepath = os.path.join(
                    #         mblab_humanoid.phenotypes_path,
                    #         "".join([obj.ethnic, ".json"]))
                    #     mblab_humanoid.load_character(filepath, mix=scn.mblab_mix_characters)
                if mblab_humanoid.exists_preset_database():
                    preset_items = algorithms.generate_items_list(mblab_humanoid.presets_path)
                    for preset in preset_items:
                        if (preset[1] == "type_normobody" or preset[1] == "type_lightbody" or preset[1] == "type_heavybody"):
                            print(preset)
                            obj = mblab_humanoid.get_object()
                            obj.preset = preset[0]
                            filepath = os.path.join(
                                mblab_humanoid.presets_path,
                                "".join([obj.preset, ".json"]))
                            mblab_humanoid.load_character(filepath, mix=scn.mblab_mix_characters)
                            # cmd = 'echo $HOME'
                            # print (subprocess.check_output(cmd, shell=True))
                            # subprocess.call('echo', shell=True)
                            # return {'FINISHED'}
                            # filename = str(uuid.uuid4())
                            filename = character[0] + '_' + preset[0]

                            basedir = os.path.join(os.path.dirname(__file__), "exports/" + character[0] + '_' + preset[0])
                            if not os.path.exists(basedir):
                                os.makedirs(basedir)
                            # basedir = os.path.dirname(bpy.data.filepath)
                            if not basedir:
                                raise Exception("Blend file is not saved")

                            png_filename = filename + ".png"
                            png_basedir = os.path.join(basedir, png_filename)
                            fn = os.path.join(basedir, filename)

                            # bpy.ops.wm.save_mainfile(filepath=fn + ".blend")

                            scn = bpy.context.scene
                            # mblab_humanoid.correct_expressions(correct_all=True)
                            mblab_humanoid.set_rest_pose()
                            mblab_humanoid.remove_modifiers()
                            mblab_humanoid.sync_internal_data_with_mesh()
                            mblab_humanoid.update_displacement()
                            mblab_humanoid.update_materials()
                            mblab_humanoid.save_backup_character(png_basedir)
                            save_metadata_json(png_basedir)
                            mblab_humanoid.save_all_textures(png_basedir)

                            mblab_humanoid.morph_engine.convert_all_to_blshapekeys()
                            mblab_humanoid.delete_all_properties()
                            mblab_humanoid.rename_materials(scn.mblab_final_prefix)
                            mblab_humanoid.update_bendy_muscles()
                            mblab_humanoid.rename_obj(scn.mblab_final_prefix)
                            mblab_humanoid.rename_armature(scn.mblab_final_prefix)

                            # Scale factor 100
                            bpy.context.area.spaces[0].pivot_point='CURSOR'
                            bpy.context.area.spaces[0].cursor_location = (0.0, 0.0, 0.0)
                            print(bpy.ops.object.mode)
                            if (bpy.ops.object.mode != 'OBJECT'):
                                bpy.ops.object.mode_set(mode='OBJECT')
                            obj = mblab_humanoid.get_object()
                            # obj.scale *= 100

                            # Load and run attached "bone_rename_script.py" script
                            text = bpy.data.texts.load(os.path.join(os.path.dirname(__file__), "bone_rename_script.py"))   # if from disk
                            ctx = bpy.context.copy()
                            ctx['edit_text'] = text
                            bpy.ops.text.run_script(ctx)
                            print("Ran bone_rename_script")

                            #Transform and save
                            scn.unit_settings.system = 'METRIC'
                            scn.unit_settings.scale_length = 0.01
                            k = 100 #scale constant
                            for ob in bpy.data.objects:
                                ob.select = True

                            bpy.ops.transform.resize(value=(k,k,k))
                            bpy.ops.object.transform_apply(scale=True)

                            bpy.ops.export_scene.fbx(filepath=fn + ".fbx", global_scale=1.0, object_types={'ARMATURE', 'MESH'}, use_mesh_modifiers=False, add_leaf_bones=False)

                            print("written:", fn)

                            # Set scene back to normal
                            # for material in bpy.data.materials:
                            #     material.user_clear()
                            #     bpy.data.materials.remove(material)
                            bpy.ops.object.delete()
                            scn.unit_settings.scale_length = 1
                            gui_status = "NEW_SESSION"
                            bpy.ops.mbast.init_character('INVOKE_DEFAULT')

        return {'FINISHED'}

class ReturnToInitScreen(bpy.types.Operator):
    bl_idname = "wellvr.return_to_init_screen"
    bl_label = "Return to Init"

    def execute(self, context):
        # Return to init
        obj = mblab_humanoid.get_object()
        name = bpy.path.clean_name(obj.name)
        if (bpy.ops.object.mode != 'OBJECT'):
            bpy.ops.object.mode_set(mode='OBJECT')
        for o in bpy.data.objects:
            if name in o.name:
                o.select = True
            else:
                o.select = False

        bpy.ops.object.delete()

        # save and re-open the file to clean up the data blocks
        # basedir = os.path.join(os.path.dirname(__file__), "automatedExports")
        # bpy.ops.wm.save_as_mainfile(filepath=basedir)
        # bpy.ops.wm.open_mainfile(filepath=basedir)
        gui_status = "NEW_SESSION"
        return{'FINISHED'}

class SwitchViewButton(bpy.types.Operator):
    bl_idname = "wellvr.switch_view_button"
    bl_label = "Switch View"

    def execute(self, context):
        global viewOnBody

        head_bone = mblab_humanoid.get_armature().data.bones.get('head')

        viewOnBody = (viewOnBody + 1) % 4
        v3d = bpy.context.space_data
        rv3d = v3d.region_3d
        if viewOnBody == 0:
            rv3d.view_distance = 2
            rv3d.view_location.z = head_bone.head_local.z - 0.5
            eul = mathutils.Euler((radians(75), 0.0, 0.0), 'XYZ')
        elif viewOnBody == 1:
            rv3d.view_distance = 0.6
            rv3d.view_location.z = head_bone.head_local.z
            eul = mathutils.Euler((radians(80), 0.0, 0.0), 'XYZ')
        elif viewOnBody == 2:
            rv3d.view_distance = 0.6
            rv3d.view_location.z = head_bone.head_local.z
            eul = mathutils.Euler((radians(80), 0.0, radians(25)), 'XYZ')
        elif viewOnBody == 3:
            rv3d.view_distance = 0.6
            rv3d.view_location.z = head_bone.head_local.z
            eul = mathutils.Euler((radians(80), 0.0, radians(-25)), 'XYZ')
        rv3d.view_rotation = eul.to_quaternion()
        return{'FINISHED'}

class TakePicturesWithCamera(bpy.types.Operator):
    bl_idname = "wellvr.take_pictures_with_camera_button"
    bl_label = "Take Pictures with Camera"
    def execute(self, context):
        if(len(bpy.data.cameras) == 1):
            camObj = bpy.data.objects['Camera']
            # Create dicts
            camLocations = {}
            camRotations = {}
            camLocations['Cheeks'] = (0.083247, -0.449644, 1.56223)
            camRotations['Cheeks'] = (88, 0, 14)
            camLocations['Chin'] = (0.152795, -0.324773, 1.48924)
            camRotations['Chin'] = (92.640, -0.00086, 33.006)
            camLocations['Ears'] = (0.237536, -0.109038, 1.55073)
            camRotations['Ears'] = (91, 0, 69.4)
            camLocations['Eyebrows'] = (0.118239, -0.303023, 1.56058)
            camRotations['Eyebrows'] = (92.9, 0, 30.8)
            camLocations['Eyelids'] = (0.118239, -0.303023, 1.56058)
            camRotations['Eyelids'] = (92.9, 0, 30.8)
            camLocations['Eyes'] = (0.047876, -0.309219, 1.5633)
            camRotations['Eyes'] = (91.8, 0, 12.6)
            camLocations['Face'] = (0.20389, -0.566657, 1.56116)
            camRotations['Face'] = (89.2, 0, 20.7)
            camLocations['Forehead'] = (0.191943, -0.453059, 1.58538)
            camRotations['Forehead'] = (90.4, 0, 26.7)
            camLocations['Head'] = (0.423361, -0.496835, 1.56154)
            camRotations['Head'] = (89.5, 0, 41.9)
            camLocations['Jaw'] = (0.123432, -0.385534, 1.54345)
            camRotations['Jaw'] = (86.3, 0, 21.6)
            camLocations['Mouth'] = (0.057212, -0.257153, 1.52886)
            camRotations['Mouth'] = (81.1, 0, 23)
            camLocations['Nose'] = (0.110908, -0.294595, 1.56963)
            camRotations['Nose'] = (83.6, 0, 33.1)
            image_count = 0
            for key, value in camLocations.items():
                print(key, value, camRotations[key])
                camObj.location = value
                x,y,z = camRotations[key]
                camObj.rotation_euler = (radians(x), radians(y), radians(z))
                for prop in mblab_humanoid.get_properties_in_category(key):
                    print(prop)
                    prop_value = 0.0;
                    while (prop_value <= 1.0):
                        image_count += 1
                        prop_value = round(prop_value, 1)
                        mblab_humanoid.character_data[prop] = prop_value
                        mblab_humanoid.update_character(category_name = key, mode="update_all")
                        prop_path = str(prop+"_"+str(prop_value))
                        file = os.path.join(os.path.dirname(__file__), "blenderpics", str(prop), prop_path)
                        print ("printing to " + file)
                        bpy.context.scene.render.filepath = file
                        bpy.ops.render.render( write_still=True )
                        prop_value += 0.1;
                    # # Get image of min prop
                    # mblab_humanoid.character_data[prop] = 0
                    # mblab_humanoid.update_character(category_name = key, mode="update_all")
                    # prop_path = str(prop+"_Min")
                    # print(prop_path)
                    # file = os.path.join(os.path.dirname(__file__), "blenderpics", prop_path)
                    # bpy.context.scene.render.filepath = file
                    # bpy.ops.render.render( write_still=True )
                    # # Get image of maxed prop
                    # mblab_humanoid.character_data[prop] = 1
                    # mblab_humanoid.update_character(category_name = key, mode="update_all")
                    # prop_path = str(prop+"_Max")
                    # print(prop_path)
                    # file = os.path.join(os.path.dirname(__file__), "blenderpics", prop_path)
                    # bpy.context.scene.render.filepath = file
                    # bpy.ops.render.render( write_still=True )
                    # Reset the prop
                    mblab_humanoid.character_data[prop] = 0.5
                    mblab_humanoid.update_character(category_name = key, mode="update_all")
                    print('\n')
            print("Total images:", image_count)
        return {'FINISHED'}

class TakeSkinPreviewPicturesWithCamera(bpy.types.Operator):
    bl_idname = "wellvr.take_skin_preview_pictures_with_camera_button"
    bl_label = "Take Skin Preview Pics"
    def execute(self, context):
        if(len(bpy.data.cameras) == 1):
            camObj = bpy.data.objects['Camera']
            # Create dicts
            camLocations = {}
            camRotations = {}
            camLocations['Skin'] = (0.151203, -1.42162, 1.43392)
            camRotations['Skin'] = (86.5, 0, 5.94)
            # Skin dicts
            skin_complexions = [0.1, 0.001, 0.650]
            skin_hues = [0.5, 0.51, 0.485]
            image_count = 1
            for key, value in camLocations.items():
                print(key, value, camRotations[key])
                camObj.location = value
                x,y,z = camRotations[key]
                camObj.rotation_euler = (radians(x), radians(y), radians(z))
                for complexion_value in skin_complexions:
                    for hue_value in skin_hues:
                        mblab_humanoid.character_material_properties['skin_complexion'] = complexion_value
                        mblab_humanoid.character_material_properties['skin_hue'] = hue_value
                        mblab_humanoid.material_realtime_activated = False
                        obj = mblab_humanoid.get_object()
                        for material_data_prop, value in mblab_humanoid.character_material_properties.items():
                            if 'skin_hue' in material_data_prop or 'skin_complexion' in material_data_prop:
                                if hasattr(obj, material_data_prop):
                                    setattr(obj, material_data_prop, value)
                                else:
                                    lab_logger.warning("material {0}  not found".format(material_data_prop))

                        mblab_humanoid.material_realtime_activated = True
                        mblab_humanoid.update_materials()

                        skin_path = str(str(image_count)+"_skin_preview_complexion-"+str(complexion_value)+"_hue-"+str(hue_value)+".png")
                        file = os.path.join(os.path.dirname(__file__), "images/generated_skin_previews", skin_path)
                        print ("printing to " + file)
                        bpy.context.scene.render.filepath = file
                        bpy.ops.render.render( write_still=True )
                        image_count += 1;

        return {'FINISHED'}

class ButtonParametersOff(bpy.types.Operator):

    bl_label = 'Body, face and measure parameters'
    bl_idname = 'mbast.button_parameters_off'
    bl_description = 'Close details panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = None
        return {'FINISHED'}

class ButtonParametersOn(bpy.types.Operator):
    bl_label = 'Body. face and measure parameters'
    bl_idname = 'mbast.button_parameters_on'
    bl_description = 'Open details panel (head,nose,hands, measures etc...)'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        global viewOnBody
        gui_active_panel = "parameters"
        sync_character_to_props()

        head_bone = mblab_humanoid.get_armature().data.bones.get('head')

        v3d = bpy.context.space_data
        rv3d = v3d.region_3d
        rv3d.view_distance = 0.6
        rv3d.view_location.z = head_bone.head_local.z
        eul = mathutils.Euler((radians(80), 0.0, 0.0), 'XYZ')
        rv3d.view_rotation = eul.to_quaternion()
        viewOnBody = 1
        return {'FINISHED'}

class ButtonUtilitiesOff(bpy.types.Operator):
    bl_label = 'UTILITIES'
    bl_idname = 'mbast.button_utilities_off'
    bl_description = 'Close utilities panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_fin
        gui_active_panel_fin = None
        return {'FINISHED'}

class ButtonUtilitiesOn(bpy.types.Operator):
    bl_label = 'UTILITIES'
    bl_idname = 'mbast.button_utilities_on'
    bl_description = 'Open utilities panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_fin
        gui_active_panel_fin = "utilities"
        return {'FINISHED'}

class ButtonExpressionsOff(bpy.types.Operator):
    bl_label = 'FACE EXPRESSIONS'
    bl_idname = 'mbast.button_expressions_off'
    bl_description = 'Close expressions panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_fin
        gui_active_panel_fin = None
        return {'FINISHED'}

class ButtonExpressionOn(bpy.types.Operator):
    bl_label = 'FACE EXPRESSIONS'
    bl_idname = 'mbast.button_expressions_on'
    bl_description = 'Open expressions panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_fin
        gui_active_panel_fin = "expressions"
        #sync_character_to_props()
        return {'FINISHED'}

class ButtonRandomOff(bpy.types.Operator):
    bl_label = 'Random generator'
    bl_idname = 'mbast.button_random_off'
    bl_description = 'Close random generator panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = None
        return {'FINISHED'}

class ButtonRandomOn(bpy.types.Operator):
    bl_label = 'Random generator'
    bl_idname = 'mbast.button_random_on'
    bl_description = 'Open random generator panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = 'random'
        sync_character_to_props()
        return {'FINISHED'}


class ButtonAutomodellingOff(bpy.types.Operator):

    bl_label = 'Automodelling tools'
    bl_idname = 'mbast.button_automodelling_off'
    bl_description = 'Close automodelling panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = None
        return {'FINISHED'}

class ButtonAutomodellingOn(bpy.types.Operator):
    bl_label = 'Automodelling tools'
    bl_idname = 'mbast.button_automodelling_on'
    bl_description = 'Open automodelling panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = 'automodelling'
        return {'FINISHED'}

class ButtoRestPoseOff(bpy.types.Operator):
    bl_label = 'Rest pose'
    bl_idname = 'mbast.button_rest_pose_off'
    bl_description = 'Close rest pose panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = None
        return {'FINISHED'}

class ButtonRestPoseOn(bpy.types.Operator):
    bl_label = 'Rest pose'
    bl_idname = 'mbast.button_rest_pose_on'
    bl_description = 'Open rest pose panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = 'rest_pose'
        return {'FINISHED'}

class ButtoPoseOff(bpy.types.Operator):
    bl_label = 'POSE AND ANIMATION'
    bl_idname = 'mbast.button_pose_off'
    bl_description = 'Close pose panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_fin
        gui_active_panel_fin = None
        return {'FINISHED'}

class ButtonAssetsOn(bpy.types.Operator):
    bl_label = 'ASSETS'
    bl_idname = 'mbast.button_assets_on'
    bl_description = 'Open assets panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_fin
        gui_active_panel_fin = 'assets'
        return {'FINISHED'}

class ButtoAssetsOff(bpy.types.Operator):
    bl_label = 'ASSETS'
    bl_idname = 'mbast.button_assets_off'
    bl_description = 'Close assets panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_fin
        gui_active_panel_fin = None
        return {'FINISHED'}

class ButtonPoseOn(bpy.types.Operator):
    bl_label = 'POSE AND ANIMATION'
    bl_idname = 'mbast.button_pose_on'
    bl_description = 'Open pose panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_fin
        gui_active_panel_fin = 'pose'
        return {'FINISHED'}


class ButtonSkinOff(bpy.types.Operator):
    bl_label = 'Skin and eyes editor'
    bl_idname = 'mbast.button_skin_off'
    bl_description = 'Close skin editor panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = None
        return {'FINISHED'}

class ButtonSkinOn(bpy.types.Operator):
    bl_label = 'Skin and eyes editor'
    bl_idname = 'mbast.button_skin_on'
    bl_description = 'Open skin editor panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        global viewOnBody
        gui_active_panel = 'skin'

        head_bone = mblab_humanoid.get_armature().data.bones.get('head')

        v3d = bpy.context.space_data
        rv3d = v3d.region_3d
        rv3d.view_distance = 0.6
        rv3d.view_location.z = head_bone.head_local.z
        eul = mathutils.Euler((radians(80), 0.0, 0.0), 'XYZ')
        rv3d.view_rotation = eul.to_quaternion()
        viewOnBody = 1
        return {'FINISHED'}

class ButtonViewOptOff(bpy.types.Operator):
    bl_label = 'Display options'
    bl_idname = 'mbast.button_display_off'
    bl_description = 'Close skin editor panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = None
        return {'FINISHED'}

class ButtonViewOptOn(bpy.types.Operator):
    bl_label = 'Display options'
    bl_idname = 'mbast.button_display_on'
    bl_description = 'Open skin editor panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = 'display_opt'
        return {'FINISHED'}



class ButtonProxyFitOff(bpy.types.Operator):
    bl_label = 'PROXY FITTING'
    bl_idname = 'mbast.button_proxy_fit_off'
    bl_description = 'Close proxy panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_fin
        gui_active_panel_fin = None
        return {'FINISHED'}

class ButtonProxyFitOn(bpy.types.Operator):
    bl_label = 'PROXY FITTING'
    bl_idname = 'mbast.button_proxy_fit_on'
    bl_description = 'Open proxy panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_fin
        gui_active_panel_fin = 'proxy_fit'
        return {'FINISHED'}


class ButtonFilesOff(bpy.types.Operator):
    bl_label = 'File tools'
    bl_idname = 'mbast.button_file_off'
    bl_description = 'Close file panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = None
        return {'FINISHED'}

class ButtonFilesOn(bpy.types.Operator):
    bl_label = 'File tools'
    bl_idname = 'mbast.button_file_on'
    bl_description = 'Open file panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = 'file'
        return {'FINISHED'}


class ButtonFinalizeOff(bpy.types.Operator):
    bl_label = 'Finalize tools'
    bl_idname = 'mbast.button_finalize_off'
    bl_description = 'Close finalize panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = None
        return {'FINISHED'}

class ButtonFinalizeOn(bpy.types.Operator):
    bl_label = 'Finalize tools'
    bl_idname = 'mbast.button_finalize_on'
    bl_description = 'Open finalize panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = 'finalize'
        return {'FINISHED'}

class ButtonLibraryOff(bpy.types.Operator):
    bl_label = 'Character library'
    bl_idname = 'mbast.button_library_off'
    bl_description = 'Close character library panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = None
        return {'FINISHED'}

class ButtonLibraryOn(bpy.types.Operator):
    bl_label = 'Character library'
    bl_idname = 'mbast.button_library_on'
    bl_description = 'Open character library panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        global viewOnBody
        gui_active_panel = 'library'

        head_bone = mblab_humanoid.get_armature().data.bones.get('head')

        v3d = bpy.context.space_data
        rv3d = v3d.region_3d
        rv3d.view_distance = 2
        rv3d.view_location.z = head_bone.head_local.z - 0.5
        eul = mathutils.Euler((radians(75), 0.0, 0.0), 'XYZ')
        rv3d.view_rotation = eul.to_quaternion()
        viewOnBody = 0
        return {'FINISHED'}

class ButtonFinalizedCorrectRot(bpy.types.Operator):
    bl_label = 'Adjust the selected bone'
    bl_idname = 'mbast.button_adjustrotation'
    bl_description = 'Correct the animation with an offset to the bone angle'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        scn = bpy.context.scene
        mblab_retarget.get_bone_rot_type()

        if mblab_retarget.rot_type in ["EULER","QUATERNION"]:
            offsets = mblab_retarget.get_offset_values()
            scn.mblab_rot_offset_0 = offsets[0]
            scn.mblab_rot_offset_1 = offsets[1]
            scn.mblab_rot_offset_2 = offsets[2]
            mblab_retarget.correction_is_sync = True
        return {'FINISHED'}

class UpdateSkinDisplacement(bpy.types.Operator):
    """
    Calculate and apply the skin displacement
    """
    bl_label = 'Update displacement'
    bl_idname = 'mbast.skindisplace_calculate'
    bl_description = 'Calculate and apply the skin details using displace modifier'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        """
        Calculate and apply the skin displacement
        """
        global mblab_humanoid
        scn = bpy.context.scene
        mblab_humanoid.update_displacement()
        mblab_humanoid.update_materials()
        return {'FINISHED'}


class DisableSubdivision(bpy.types.Operator):
    """
    Disable subdivision surface
    """
    bl_label = 'Disable subdivision preview'
    bl_idname = 'mbast.subdivision_disable'
    bl_description = 'Disable subdivision modifier'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):

        global mblab_humanoid
        scn = bpy.context.scene

        if mblab_humanoid.get_subd_visibility() == True:
            mblab_humanoid.set_subd_visibility(False)
        return {'FINISHED'}

class EnableSubdivision(bpy.types.Operator):
    """
    Enable subdivision surface
    """
    bl_label = 'Enable subdivision preview'
    bl_idname = 'mbast.subdivision_enable'
    bl_description = 'Enable subdivision preview (Warning: it will slow down the morphing)'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):

        global mblab_humanoid
        scn = bpy.context.scene

        if mblab_humanoid.get_subd_visibility() == False:
            mblab_humanoid.set_subd_visibility(True)
        return {'FINISHED'}

class DisableSmooth(bpy.types.Operator):

    bl_label = 'Disable corrective smooth'
    bl_idname = 'mbast.corrective_disable'
    bl_description = 'Disable corrective smooth modifier in viewport'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):

        global mblab_humanoid
        scn = bpy.context.scene

        if mblab_humanoid.get_smooth_visibility() == True:
            mblab_humanoid.set_smooth_visibility(False)
        return {'FINISHED'}

class EnableSmooth(bpy.types.Operator):

    bl_label = 'Enable corrective smooth'
    bl_idname = 'mbast.corrective_enable'
    bl_description = 'Enable corrective smooth modifier in viewport'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):

        global mblab_humanoid
        scn = bpy.context.scene

        if mblab_humanoid.get_smooth_visibility() == False:
            mblab_humanoid.set_smooth_visibility(True)
        return {'FINISHED'}

class DisableDisplacement(bpy.types.Operator):
    """
    Disable displacement modifier
    """
    bl_label = 'Disable displacement preview'
    bl_idname = 'mbast.displacement_disable'
    bl_description = 'Disable displacement modifier'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):

        global mblab_humanoid
        scn = bpy.context.scene

        if mblab_humanoid.get_disp_visibility() == True:
            mblab_humanoid.set_disp_visibility(False)
        return {'FINISHED'}

class EnableDisplacement(bpy.types.Operator):
    """
    Enable displacement modifier
    """
    bl_label = 'Enable displacement preview'
    bl_idname = 'mbast.displacement_enable'
    bl_description = 'Enable displacement preview (Warning: it will slow down the morphing)'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):

        global mblab_humanoid
        scn = bpy.context.scene

        if mblab_humanoid.get_disp_visibility() == False:
            mblab_humanoid.set_disp_visibility(True)
        return {'FINISHED'}


class FinalizeCharacterAndImages(bpy.types.Operator,ExportHelper):
    """
        Convert the character in a standard Blender model
    """
    bl_label = 'Finalize with textures and backup'
    bl_idname = 'mbast.finalize_character_and_images'
    filename_ext = ".png"
    filter_glob = bpy.props.StringProperty(
        default="*.png",
        options={'HIDDEN'},
        )
    bl_description = 'Finalize, saving all the textures and converting the parameters in shapekeys. Warning: after the conversion the character will be no longer modifiable using ManuelbastioniLAB tools'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):

        global mblab_humanoid
        global gui_status
        #TODO unique function in humanoid class
        scn = bpy.context.scene
        armature = mblab_humanoid.get_armature()

        mblab_humanoid.correct_expressions(correct_all=True)

        if not algorithms.is_IK_armature(armature):
            mblab_humanoid.set_rest_pose()
        if scn.mblab_remove_all_modifiers:
            mblab_humanoid.remove_modifiers()

        mblab_humanoid.sync_internal_data_with_mesh()
        mblab_humanoid.update_displacement()
        mblab_humanoid.update_materials()
        mblab_humanoid.save_backup_character(self.filepath)
        mblab_humanoid.save_all_textures(self.filepath)

        mblab_humanoid.morph_engine.convert_all_to_blshapekeys()
        mblab_humanoid.delete_all_properties()
        mblab_humanoid.rename_materials(scn.mblab_final_prefix)
        mblab_humanoid.update_bendy_muscles()
        mblab_humanoid.rename_obj(scn.mblab_final_prefix)
        mblab_humanoid.rename_armature(scn.mblab_final_prefix)
        gui_status = "AFTER_CREATION"
        return {'FINISHED'}

class FinalizeCharacter(bpy.types.Operator):
    """
    Convert the character in a standard Blender model
    """
    bl_label = 'Finalize'
    bl_idname = 'mbast.finalize_character'
    bl_description = 'Finalize converting the parameters in shapekeys. Warning: after the conversion the character will be no longer modifiable using ManuelbastioniLAB tools'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):

        global mblab_humanoid
        global gui_status
        scn = bpy.context.scene
        armature = mblab_humanoid.get_armature()

        mblab_humanoid.correct_expressions(correct_all=True)


        if not algorithms.is_IK_armature(armature):
            mblab_humanoid.set_rest_pose()
        if scn.mblab_remove_all_modifiers:
            mblab_humanoid.remove_modifiers()

        mblab_humanoid.sync_internal_data_with_mesh()

        mblab_humanoid.morph_engine.convert_all_to_blshapekeys()
        mblab_humanoid.update_displacement()
        mblab_humanoid.update_materials()

        mblab_humanoid.delete_all_properties()
        mblab_humanoid.rename_materials(scn.mblab_final_prefix)
        mblab_humanoid.update_bendy_muscles()
        mblab_humanoid.rename_obj(scn.mblab_final_prefix)
        mblab_humanoid.rename_armature(scn.mblab_final_prefix)


        gui_status = "AFTER_CREATION"
        return {'FINISHED'}


class WellVRFinalizeCharacterAndMetadata(bpy.types.Operator):
    """
        Convert the character in a standard Blender model
    """
    bl_label = 'Finalize with metadata and backup'
    bl_idname = 'wellvr.finalize_character_and_metadata'
    # filename_ext = ".png"
    # filter_glob = bpy.props.StringProperty(
    #     default="*.png",
    #     options={'HIDDEN'},
    #     )
    bl_description = 'Finalize, saving all the textures and converting the parameters in shapekeys. Warning: after the conversion the character will be no longer modifiable using ManuelbastioniLAB tools'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        col = self.layout.column(align = True)
        col.prop(context.scene, "name_input_prop")

    def execute(self, context):

        global mblab_humanoid
        global gui_status
        #TODO unique function in humanoid class
        scn = bpy.context.scene
        armature = mblab_humanoid.get_armature()

        filename = context.scene.name_input_prop
        if (filename == ''):
            self.report({'INFO'}, "Please enter a name for the character")
            return {'CANCELLED'}
        ex = filename.rstrip()
        if (not re.match(r'^[a-zA-Z0-9][ A-Za-z0-9_-]*$', ex)):
            self.report({'INFO'}, "Alphanumeric characters and underscores only")
            return {'CANCELLED'}

        basedir = os.path.join(os.path.dirname(__file__), "exports/" + context.scene.name_input_prop)
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        # basedir = os.path.dirname(bpy.data.filepath)
        if not basedir:
            raise Exception("Blend file is not saved")

        png_filename = filename + ".png"
        png_basedir = os.path.join(basedir, png_filename)

        mblab_humanoid.correct_expressions(correct_all=True)
        # if not algorithms.is_IK_armature(armature):
        mblab_humanoid.set_rest_pose()
        # if scn.mblab_remove_all_modifiers:
        mblab_humanoid.remove_modifiers()
        mblab_humanoid.sync_internal_data_with_mesh()
        mblab_humanoid.update_displacement()
        mblab_humanoid.update_materials()
        mblab_humanoid.save_backup_character(png_basedir)
        save_metadata_json(png_basedir)
        mblab_humanoid.save_all_textures(png_basedir)

        mblab_humanoid.morph_engine.convert_all_to_blshapekeys()
        mblab_humanoid.delete_all_properties()
        mblab_humanoid.rename_materials(scn.mblab_final_prefix)
        mblab_humanoid.update_bendy_muscles()
        mblab_humanoid.rename_obj(scn.mblab_final_prefix)
        mblab_humanoid.rename_armature(scn.mblab_final_prefix)
        gui_status = "AFTER_CREATION"
        return {'FINISHED'}


class ResetParameters(bpy.types.Operator):
    """
    Reset all morphings.
    """
    bl_label = 'Reset character'
    bl_idname = 'mbast.reset_allproperties'
    bl_description = 'Reset all character parameters'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL','UNDO'}

    def execute(self, context):
        global mblab_humanoid
        mblab_humanoid.reset_character()
        return {'FINISHED'}

class ResetExpressions(bpy.types.Operator):
    """
    Reset all morphings.
    """
    bl_label = 'Reset Expression'
    bl_idname = 'mbast.reset_expression'
    bl_description = 'Reset the expression'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL','UNDO'}

    def execute(self, context):
        global mblab_shapekeys
        mblab_shapekeys.reset_expressions_GUI()
        return {'FINISHED'}

class LoadAssets(bpy.types.Operator):
    """
    Load assets from library
    """
    bl_label = 'Load element from library'
    bl_idname = 'mbast.load_assets_element'
    bl_description = 'Load the element selected from the assets library'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL','UNDO'}

    def execute(self, context):
        scn = bpy.context.scene
        mblab_proxy.load_asset(scn.mblab_assets_models)
        return {'FINISHED'}


class InsertExpressionKeyframe(bpy.types.Operator):
    """
    Reset all morphings.
    """
    bl_label = 'Insert Keyframe'
    bl_idname = 'mbast.keyframe_expression'
    bl_description = 'Insert a keyframe expression at the current time'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL','UNDO'}

    def execute(self, context):
        global mblab_shapekeys
        mblab_shapekeys.keyframe_expression()
        return {'FINISHED'}


class Reset_category(bpy.types.Operator):
    """
    Reset the parameters for the currently selected category
    """
    bl_label = 'Reset category'
    bl_idname = 'mbast.reset_categoryonly'
    bl_description = 'Reset the parameters for the current category'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL','UNDO'}

    def execute(self, context):
        global mblab_humanoid
        scn = bpy.context.scene
        mblab_humanoid.reset_category(scn.morphingCategory)
        return {'FINISHED'}


class CharacterGenerator(bpy.types.Operator):
    """
    Generate a new character using the specified parameters.
    """
    bl_label = 'Generate'
    bl_idname = 'mbast.character_generator'
    bl_description = 'Generate a new character according the parameters.'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL','UNDO'}

    def execute(self, context):
        global mblab_humanoid
        scn = bpy.context.scene
        rnd_values = {"LI": 0.05, "RE": 0.1, "NO": 0.2, "CA":0.3, "EX": 0.5}
        rnd_val = rnd_values[scn.mblab_random_engine]
        p_face = scn.mblab_preserve_face
        p_body = scn.mblab_preserve_body
        p_mass = scn.mblab_preserve_mass
        p_tone = scn.mblab_preserve_tone
        p_height = scn.mblab_preserve_height
        p_phenotype = scn.mblab_preserve_phenotype
        set_tone_mass = scn.mblab_set_tone_and_mass
        b_tone = scn.mblab_body_tone
        b_mass = scn.mblab_body_mass
        p_fantasy = scn.mblab_preserve_fantasy

        mblab_humanoid.generate_character(rnd_val,p_face,p_body,p_mass,p_tone,p_height,p_phenotype,set_tone_mass,b_mass,b_tone,p_fantasy)
        return {'FINISHED'}

class ExpDisplacementImage(bpy.types.Operator, ExportHelper):
    """Export parameters for the character"""
    bl_idname = "mbast.export_dispimage"
    bl_label = "Save displacement image"
    filename_ext = ".png"
    filter_glob = bpy.props.StringProperty(
        default="*.png",
        options={'HIDDEN'},
        )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_humanoid
        mblab_humanoid.save_body_displacement_texture(self.filepath)
        return {'FINISHED'}

class ExpDermalImage(bpy.types.Operator, ExportHelper):
    """Export parameters for the character"""
    bl_idname = "mbast.export_dermimage"
    bl_label = "Save dermal image"
    filename_ext = ".png"
    filter_glob = bpy.props.StringProperty(
        default="*.png",
        options={'HIDDEN'},
        )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_humanoid
        mblab_humanoid.save_body_dermal_texture(self.filepath)
        return {'FINISHED'}


class ExpAllImages(bpy.types.Operator, ExportHelper):
    """
    """
    bl_idname = "mbast.export_allimages"
    bl_label = "Export all images"
    filename_ext = ".png"
    filter_glob = bpy.props.StringProperty(
        default="*.png",
        options={'HIDDEN'},
        )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_humanoid
        mblab_humanoid.save_all_textures(self.filepath)
        return {'FINISHED'}



class ExpCharacter(bpy.types.Operator, ExportHelper):
    """Export parameters for the character"""
    bl_idname = "mbast.export_character"
    bl_label = "Export character"
    filename_ext = ".json"
    filter_glob = bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
        )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_humanoid
        scn = bpy.context.scene
        mblab_humanoid.save_character(self.filepath, scn.mblab_export_proportions, scn.mblab_export_materials)
        return {'FINISHED'}

class ExpMeasures(bpy.types.Operator, ExportHelper):
    """Export parameters for the character"""
    bl_idname = "mbast.export_measures"
    bl_label = "Export measures"
    filename_ext = ".json"
    filter_glob = bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
        )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_humanoid
        mblab_humanoid.export_measures(self.filepath)
        return {'FINISHED'}


class ImpCharacter(bpy.types.Operator, ImportHelper):
    """
    Import parameters for the character
    """
    bl_idname = "mbast.import_character"
    bl_label = "Import character"
    filename_ext = ".json"
    filter_glob = bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
        )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_humanoid

        char_data = mblab_humanoid.load_character(self.filepath)
        return {'FINISHED'}

class ImpMeasures(bpy.types.Operator, ImportHelper):
    """
    Import parameters for the character
    """
    bl_idname = "mbast.import_measures"
    bl_label = "Import measures"
    filename_ext = ".json"
    filter_glob = bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
        )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_humanoid
        mblab_humanoid.import_measures(self.filepath)
        return {'FINISHED'}


class LoadDermImage(bpy.types.Operator, ImportHelper):
    """

    """
    bl_idname = "mbast.import_dermal"
    bl_label = "Load dermal image"
    filename_ext = ".png"
    filter_glob = bpy.props.StringProperty(
        default="*.png",
        options={'HIDDEN'},
        )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_humanoid
        mblab_humanoid.load_body_dermal_texture(self.filepath)
        return {'FINISHED'}


class LoadDispImage(bpy.types.Operator, ImportHelper):
    """

    """
    bl_idname = "mbast.import_displacement"
    bl_label = "Load displacement image"
    filename_ext = ".png"
    filter_glob = bpy.props.StringProperty(
        default="*.png",
        options={'HIDDEN'},
        )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_humanoid
        mblab_humanoid.load_body_displacement_texture(self.filepath)
        return {'FINISHED'}
class FitProxy(bpy.types.Operator):

    bl_label = 'Fit Proxy'
    bl_idname = 'mbast.proxy_fit'
    bl_description = 'Fit the selected proxy to the character'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        scn = bpy.context.scene
        offset = scn.mblab_proxy_offset/1000
        threshold = scn.mblab_proxy_threshold/1000
        mblab_proxy.fit_proxy_object(offset, threshold, scn.mblab_add_mask_group, True, scn.mblab_overwrite_proxy_weights)
        return {'FINISHED'}

class RemoveProxy(bpy.types.Operator):

    bl_label = 'Remove fitting'
    bl_idname = 'mbast.proxy_removefit'
    bl_description = 'Remove fitting, so the proxy can be modified and then fitted again'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        scn = bpy.context.scene
        mblab_proxy.remove_fitting()
        return {'FINISHED'}

class ApplyMeasures(bpy.types.Operator):
    """
    Fit the character to the measures
    """

    bl_label = 'Update character'
    bl_idname = 'mbast.measures_apply'
    bl_description = 'Fit the character to the measures'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global mblab_humanoid
        mblab_humanoid.automodelling(use_measures_from_GUI=True)
        return {'FINISHED'}


class AutoModelling(bpy.types.Operator):
    """
    Fit the character to the measures
    """

    bl_label = 'Auto modelling'
    bl_idname = 'mbast.auto_modelling'
    bl_description = 'Analyze the mesh form and return a verisimilar human'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL','UNDO'}

    def execute(self, context):
        global mblab_humanoid
        mblab_humanoid.automodelling(use_measures_from_current_obj=True)
        return {'FINISHED'}

class AutoModellingMix(bpy.types.Operator):
    """
    Fit the character to the measures
    """

    bl_label = 'Averaged auto modelling'
    bl_idname = 'mbast.auto_modelling_mix'
    bl_description = 'Return a verisimilar human with multiple interpolations that make it nearest to average'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL','UNDO'}

    def execute(self, context):
        global mblab_humanoid
        mblab_humanoid.automodelling(use_measures_from_current_obj=True, mix = True)
        return {'FINISHED'}

class SaveRestPose(bpy.types.Operator, ExportHelper):
    """Export pose"""
    bl_idname = "mbast.restpose_save"
    bl_label = "Save custom rest pose"
    filename_ext = ".json"
    filter_glob = bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
        )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_humanoid
        armature = mblab_humanoid.get_armature()
        mblab_retarget.save_pose(armature, self.filepath)
        return {'FINISHED'}

class LoadRestPose(bpy.types.Operator, ImportHelper):
    """
    Import parameters for the character
    """
    bl_idname = "mbast.restpose_load"
    bl_label = "Load custom rest pose"
    filename_ext = ".json"
    filter_glob = bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
        )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_humanoid, mblab_retarget
        armature = mblab_humanoid.get_armature()
        mblab_retarget.load_pose(self.filepath, armature, use_retarget = False)
        return {'FINISHED'}


class SavePose(bpy.types.Operator, ExportHelper):
    """Export pose"""
    bl_idname = "mbast.pose_save"
    bl_label = "Save pose"
    filename_ext = ".json"
    filter_glob = bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
        )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_humanoid
        armature = algorithms.get_active_armature()
        mblab_retarget.save_pose(armature, self.filepath)
        return {'FINISHED'}

class LoadPose(bpy.types.Operator, ImportHelper):
    """
    Import parameters for the character
    """
    bl_idname = "mbast.pose_load"
    bl_label = "Load pose"
    filename_ext = ".json"
    filter_glob = bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
        )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_retarget
        mblab_retarget.load_pose(self.filepath, use_retarget = True)
        return {'FINISHED'}

class ResetPose(bpy.types.Operator):
    """
    Import parameters for the character
    """
    bl_idname = "mbast.pose_reset"
    bl_label = "Reset pose"
    bl_context = 'objectmode'
    bl_description = 'Reset the angles of the armature bones'
    bl_options = {'REGISTER', 'INTERNAL','UNDO'}

    def execute(self, context):
        global mblab_retarget
        mblab_retarget.reset_pose()
        return {'FINISHED'}


class LoadBvh(bpy.types.Operator, ImportHelper):
    """
    Import parameters for the character
    """
    bl_idname = "mbast.load_animation"
    bl_label = "Load animation (bvh)"
    filename_ext = ".bvh"
    bl_description = 'Import the animation from a bvh motion capture file'
    filter_glob = bpy.props.StringProperty(
        default="*.bvh",
        options={'HIDDEN'},
        )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_retarget
        mblab_retarget.load_animation(self.filepath)
        return {'FINISHED'}



class StartSession(bpy.types.Operator):
    bl_idname = "mbast.init_character"
    bl_label = "Init character"
    bl_description = 'Create the character selected above'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL','UNDO'}

    def execute(self, context):
        start_lab_session()
        return {'FINISHED'}


class LoadTemplate(bpy.types.Operator):
    bl_idname = "mbast.load_base_template"
    bl_label = "Import template"
    bl_description = 'Import the humanoid template for proxies reference'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL','UNDO'}

    def execute(self, context):
        global mblab_humanoid
        scn = bpy.context.scene
        lib_filepath = algorithms.get_blendlibrary_path()
        base_model_name = mblab_humanoid.characters_config[scn.mblab_template_name]["template_model"]
        obj = algorithms.import_object_from_lib(lib_filepath, base_model_name, scn.mblab_template_name)
        if obj:
            obj["manuellab_proxy_reference"] = mblab_humanoid.characters_config[scn.mblab_template_name]["template_model"]
        return {'FINISHED'}


class VIEW3D_PT_tools_ManuelbastioniLAB(bpy.types.Panel):

    bl_label = "EasyBastioniLAB"
    bl_idname = "OBJECT_PT_characters01"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    #bl_context = 'objectmode'
    bl_category = "EasyBastioniLAB"

    @classmethod
    def poll(cls, context):
        return context.mode in {'OBJECT', 'POSE'}

    def draw(self, context):

        global mblab_humanoid,gui_status,gui_err_msg,gui_active_panel
        scn = bpy.context.scene
        icon_expand = "DISCLOSURE_TRI_RIGHT"
        icon_collapse = "DISCLOSURE_TRI_DOWN"

        if gui_status == "ERROR_SESSION":
            box = self.layout.box()
            box.label(gui_err_msg, icon="INFO")

        if gui_status == "NEW_SESSION":
            #box = self.layout.box()

            # self.layout.label("www.manuelbastioni.com")
            self.layout.label("CREATION TOOLS")
            self.layout.prop(scn, 'mblab_character_name')

            # if advanced_mode_is_on:
            if mblab_humanoid.is_ik_rig_available(scn.mblab_character_name):
                self.layout.prop(scn,'mblab_use_ik')
            if mblab_humanoid.is_muscle_rig_available(scn.mblab_character_name):
                self.layout.prop(scn,'mblab_use_muscle')

            self.layout.prop(scn,'mblab_use_cycles')
            if scn.mblab_use_cycles:
                self.layout.prop(scn,'mblab_use_lamps')

            self.layout.operator('mbast.init_character')
            # uncomment this to export characters -- EasyBastioniLAB -- wellvr
            # self.layout.operator('wellvr.export_character_presets_button')

        if gui_status == "AFTER_CREATION":
            # if advanced_mode_is_on:
            self.layout.label(" ")
            self.layout.label("AFTER-CREATION TOOLS")


            if gui_active_panel_fin != "assets":
                self.layout.operator('mbast.button_assets_on', icon=icon_expand)
            else:
                self.layout.operator('mbast.button_assets_off', icon=icon_collapse)
                #assets_status = mblab_proxy.validate_assets_fitting()
                box = self.layout.box()
                box.prop(scn,'mblab_assets_models')
                box.operator('mbast.load_assets_element')


            if advanced_mode_is_on:
                if gui_active_panel_fin != "pose":
                    self.layout.operator('mbast.button_pose_on', icon=icon_expand)
                else:
                    self.layout.operator('mbast.button_pose_off', icon=icon_collapse)
                    box = self.layout.box()

                    armature = algorithms.get_active_armature()
                    if armature != None and algorithms.is_IK_armature(armature) != True:
                        box.enabled = True
                        sel_gender = algorithms.get_selected_gender()
                        if sel_gender == "FEMALE":
                            if mblab_retarget.femaleposes_exist:
                                box.prop(armature, "female_pose")
                        if sel_gender == "MALE":
                            if mblab_retarget.maleposes_exist:
                                box.prop(armature, "male_pose")
                        box.operator("mbast.pose_load", icon='IMPORT')
                        box.operator("mbast.pose_save", icon='EXPORT')
                        box.operator("mbast.pose_reset", icon='ARMATURE_DATA')
                        box.operator("mbast.load_animation", icon='IMPORT')
                    else:
                        box.enabled = False
                        box.label("Please select the lab character (IK not supported)", icon = 'INFO')

                if gui_active_panel_fin != "expressions":
                    self.layout.operator('mbast.button_expressions_on', icon=icon_expand)
                else:
                    self.layout.operator('mbast.button_expressions_off', icon=icon_collapse)
                    box = self.layout.box()
                    mblab_shapekeys.update_expressions_data()
                    if mblab_shapekeys.model_type != "NONE":
                        box.enabled = True
                        box.prop(scn, 'mblab_expression_filter')
                        box.operator("mbast.keyframe_expression", icon="ACTION")
                        if mblab_shapekeys.expressions_data:
                            obj = algorithms.get_active_body()
                            for expr_name in sorted(mblab_shapekeys.expressions_data.keys()):
                                if hasattr(obj, expr_name):
                                    if scn.mblab_expression_filter in expr_name:
                                        box.prop(obj, expr_name)
                        box.operator("mbast.reset_expression", icon="RECOVER_AUTO")
                    else:
                        box.enabled = False
                        box.label("No express. shapekeys", icon = 'INFO')

            if gui_active_panel_fin != "proxy_fit":
                self.layout.operator('mbast.button_proxy_fit_on', icon=icon_expand)
            else:
                self.layout.operator('mbast.button_proxy_fit_off', icon=icon_collapse)
                fitting_status, proxy_obj, reference_obj = mblab_proxy.validate_proxy_fitting()

                box = self.layout.box()
                box.label("PROXY FITTING")

                if fitting_status == "NO_REFERENCE":
                    box.enabled = False
                    box.label("Fitting not available for selected objects.", icon="INFO")
                    box.label("Possible reasons:")
                    box.label("- Body created with a different lab version")
                    box.label("- Body topology modified by custom modelling")
                    box.label("- Selection of a non-mesh object")
                    box.label("- Body topology altered by modifiers (decimator,subsurf, etc..)")
                if fitting_status == 'OK':
                    box.enabled = True
                    box.label("The proxy is ready for fitting.", icon="INFO")
                    proxy_compatib = mblab_proxy.validate_assets_compatibility(proxy_obj, reference_obj)
                    if proxy_compatib == "WARNING":
                        box.label("The proxy is not designed for the selected character.", icon="ERROR")


                    box.prop(scn,'mblab_proxy_offset')
                    box.prop(scn,'mblab_proxy_threshold')
                    box.prop(scn, 'mblab_add_mask_group')
                    box.prop(scn, 'mblab_overwrite_proxy_weights')
                    box.operator("mbast.proxy_fit", icon="MOD_CLOTH")
                    box.operator("mbast.proxy_removefit", icon="MOD_CLOTH")
                if fitting_status == 'WRONG_SELECTION':
                    box.enabled = False
                    box.label("Please select only two objects: humanoid and proxy", icon="INFO")
                if fitting_status == 'NO_REFERENCE_SELECTED':
                    box.enabled = False
                    box.label("No valid humanoid template selected", icon="INFO")
                if fitting_status == 'NO_MESH_SELECTED':
                    box.enabled = False
                    box.label("Selected proxy is not a mesh", icon="INFO")

            if advanced_mode_is_on:
                if gui_active_panel_fin != "utilities":
                    self.layout.operator('mbast.button_utilities_on', icon=icon_expand)
                else:
                    self.layout.operator('mbast.button_utilities_off', icon=icon_collapse)

                    box = self.layout.box()
                    box.label("Choose a proxy reference")
                    box.prop(scn, 'mblab_template_name')
                    box.operator('mbast.load_base_template')

                    box = self.layout.box()
                    box.label("Bones rot. offset")
                    box.operator('mbast.button_adjustrotation', icon='BONE_DATA')
                    mblab_retarget.check_correction_sync()
                    if mblab_retarget.is_animated_bone == "VALID_BONE":
                        if mblab_retarget.correction_is_sync:
                                box.prop(scn,'mblab_rot_offset_0')
                                box.prop(scn,'mblab_rot_offset_1')
                                box.prop(scn,'mblab_rot_offset_2')
                    else:
                        box.label(mblab_retarget.is_animated_bone)

            self.layout.operator('wellvr.export_to_unreal', icon='FILE_TICK')


        if gui_status == "ACTIVE_SESSION":
            obj = mblab_humanoid.get_object()
            armature = mblab_humanoid.get_armature()
            if obj and armature:
                #box = self.layout.box()

                if mblab_humanoid.exists_transform_database():
                    if advanced_mode_is_on:
                        self.layout.label("CREATION TOOLS")
                        x_age = getattr(obj,'character_age',0)
                        x_mass = getattr(obj,'character_mass',0)
                        x_tone = getattr(obj,'character_tone',0)
                        age_lbl = round((15.5*x_age**2)+31*x_age+33)
                        mass_lbl = round(50*(x_mass+1))
                        tone_lbl = round(50*(x_tone+1))
                        lbl_text = "Age: {0}y  Mass: {1}%  Tone: {2}% ".format(age_lbl,mass_lbl,tone_lbl)
                        self.layout.label(lbl_text,icon="RNA")
                        for meta_data_prop in sorted(mblab_humanoid.character_metaproperties.keys()):
                            if "last" not in meta_data_prop:
                                self.layout.prop(obj, meta_data_prop)
                    self.layout.operator("mbast.reset_allproperties", icon="LOAD_FACTORY")
                    if advanced_mode_is_on:
                        if mblab_humanoid.get_subd_visibility() == True:
                            self.layout.label("Tip: for slow PC, disable the subdivision in Display Options below", icon='INFO')

                if gui_active_panel != "library":
                    self.layout.operator('mbast.button_library_on', icon=icon_expand)
                else:
                    self.layout.operator('mbast.button_library_off', icon=icon_collapse)
                    box = self.layout.box()

                    box.label("Characters library")
                    if mblab_humanoid.exists_preset_database():
                        box.prop(obj, "preset")
                    if mblab_humanoid.exists_phenotype_database():
                        box.prop(obj, "ethnic")
                    if advanced_mode_is_on:
                        box.prop(scn, 'mblab_mix_characters')

                if advanced_mode_is_on:
                    if gui_active_panel != "random":
                        self.layout.operator('mbast.button_random_on', icon=icon_expand)
                    else:
                        self.layout.operator('mbast.button_random_off', icon=icon_collapse)

                        box = self.layout.box()
                        box.prop(scn, "mblab_random_engine")
                        box.prop(scn, "mblab_set_tone_and_mass")
                        if scn.mblab_set_tone_and_mass:
                            box.prop(scn, "mblab_body_mass")
                            box.prop(scn, "mblab_body_tone")

                        box.label("Preserve:")
                        box.prop(scn, "mblab_preserve_mass")
                        box.prop(scn, "mblab_preserve_height")
                        box.prop(scn, "mblab_preserve_tone")
                        box.prop(scn, "mblab_preserve_body")
                        box.prop(scn, "mblab_preserve_face")
                        box.prop(scn, "mblab_preserve_phenotype")
                        box.prop(scn, "mblab_preserve_fantasy")

                        box.operator('mbast.character_generator', icon="FILE_REFRESH")

                if gui_active_panel != "parameters":
                    self.layout.operator('mbast.button_parameters_on', icon=icon_expand)
                else:
                    self.layout.operator('mbast.button_parameters_off', icon=icon_collapse)

                    box = self.layout.box()
                    mblab_humanoid.bodydata_realtime_activated = True
                    # if mblab_humanoid.exists_measure_database():
                    #     box.prop(scn, 'mblab_show_measures')
                    split = box.split()

                    col = split.column()
                    col2 = split.column()
                    col.label("PARAMETERS")
                    col2.prop(scn, "morphingCategory")



                    for prop in mblab_humanoid.get_shortlist_properties_in_category(scn.morphingCategory):
                        if hasattr(obj, prop):
                            row = col.row()
                            row.template_icon_view(scn, prop, show_labels=False, scale=10.0)
                            row2 = col.row()
                            row2.label(prop)
                            # row.scale_y = 2.5
                            # prop_name = prop.replace("_", " ")
                            # row.operator("wellvr.generic_morph_button_minus", text=prop_name+" Min", icon_value=custom_icons["custom_icon"].icon_id).morphtargetprop = prop
                            # row2 = col2.row()
                            # row2.scale_y = 2.5
                            # row2.operator("wellvr.generic_morph_button_plus", text=prop_name+" Max", icon_value=custom_icons["custom_icon"].icon_id).morphtargetprop = prop

                    if mblab_humanoid.exists_measure_database() and scn.mblab_show_measures:
                        col = split.column()
                        col.label("DIMENSIONS")
                        col.label("Experimental feature", icon = 'ERROR')
                        col.prop(obj, 'mblab_use_inch')
                        col.prop(scn, 'mblab_measure_filter')
                        col.operator("mbast.measures_apply")

                        m_unit = "cm"
                        if obj.mblab_use_inch:
                            m_unit = "Inches"
                        col.label("Height: {0} {1}".format(round(getattr(obj, "body_height_Z", 0),3),m_unit))
                        for measure in sorted(mblab_humanoid.measures.keys()):
                            if measure != "body_height_Z":
                                if hasattr(obj, measure):
                                    if scn.mblab_measure_filter in measure:
                                        col.prop(obj, measure)

                        col.operator("mbast.export_measures", icon='EXPORT')
                        col.operator("mbast.import_measures", icon='IMPORT')

                    sub = box.box()
                    sub.label("RESET")
                    sub.operator("mbast.reset_categoryonly")

                if advanced_mode_is_on:
                    if mblab_humanoid.exists_measure_database():
                        if gui_active_panel != "automodelling":
                            self.layout.operator('mbast.button_automodelling_on', icon=icon_expand)
                        else:
                            self.layout.operator('mbast.button_automodelling_off', icon=icon_collapse)
                            box = self.layout.box()
                            box.operator("mbast.auto_modelling")
                            box.operator("mbast.auto_modelling_mix")
                    else:
                        box = self.layout.box()
                        box.enabled = False
                        box.label("Automodelling not available for this character", icon='INFO')

                # if mblab_humanoid.exists_rest_poses_database():
                #     if gui_active_panel != "rest_pose":
                #         self.layout.operator('mbast.button_rest_pose_on', icon=icon_expand)
                #     else:
                #         self.layout.operator('mbast.button_rest_pose_off', icon=icon_collapse)
                #         box = self.layout.box()
                #
                #         if algorithms.is_IK_armature(armature):
                #             box.enabled = False
                #             box.label("Rest poses are not available for IK armatures", icon='INFO')
                #         else:
                #             box.enabled = True
                #             box.prop(armature, "rest_pose")
                #
                #             box.operator("mbast.restpose_load")
                #             box.operator("mbast.restpose_save")

                if advanced_mode_is_on:
                    if gui_active_panel != "skin":
                        self.layout.operator('mbast.button_skin_on', icon=icon_expand)
                    else:
                        self.layout.operator('mbast.button_skin_off', icon=icon_collapse)

                        box = self.layout.box()
                        box.enabled = True
                        if scn.render.engine != 'CYCLES':
                            box.enabled = False
                            box.label("Skin editor requires Cycles", icon='INFO')

                        if mblab_humanoid.exists_displace_texture():
                            box.operator("mbast.skindisplace_calculate")
                            box.label("You need to enable subdiv and displ to see the displ in viewport", icon='INFO')

                        for material_data_prop in sorted(mblab_humanoid.character_material_properties.keys()):
                            box.prop(obj, material_data_prop)

                        box.prop(scn, 'mblab_show_texture_load_save')
                        if scn.mblab_show_texture_load_save:

                            if mblab_humanoid.exists_dermal_texture():
                                sub = box.box()
                                sub.label("Dermal texture")
                                sub.operator("mbast.export_dermimage", icon='EXPORT')
                                sub.operator("mbast.import_dermal", icon='IMPORT')

                            if mblab_humanoid.exists_displace_texture():
                                sub = box.box()
                                sub.label("Displacement texture")
                                sub.operator("mbast.export_dispimage", icon='EXPORT')
                                sub.operator("mbast.import_displacement", icon='IMPORT')

                            sub = box.box()
                            sub.label("Export all images used in skin shader")
                            sub.operator("mbast.export_allimages", icon='EXPORT')

                # advanced_mode_is_on is false; show the skin and eye previews
                else:
                    if gui_active_panel != "skin":
                        self.layout.operator('mbast.button_skin_on', icon=icon_expand)
                    else:
                        self.layout.operator('mbast.button_skin_off', icon=icon_collapse)
                        row = self.layout.row()
                        row.template_icon_view(scn, "skin_previews", show_labels=False, scale=10.0)


                if advanced_mode_is_on:
                    if gui_active_panel != "file":
                        self.layout.operator('mbast.button_file_on', icon=icon_expand)
                    else:
                        self.layout.operator('mbast.button_file_off', icon=icon_collapse)
                        box = self.layout.box()
                        box.prop(scn, 'mblab_export_proportions')
                        box.prop(scn, 'mblab_export_materials')
                        box.operator("mbast.export_character", icon='EXPORT')
                        box.operator("mbast.import_character", icon='IMPORT')

                self.layout.operator('wellvr.switch_view_button',icon='CAMERA_DATA')
                # if advanced_mode_is_on:
                if gui_active_panel != "finalize":
                    self.layout.operator('mbast.button_finalize_on', icon=icon_expand)
                else:
                    self.layout.operator('mbast.button_finalize_off', icon=icon_collapse)
                    box = self.layout.box()
                    box.operator("wellvr.finalize_character_and_metadata", icon='FREEZE')
                    # box.prop(scn, 'mblab_save_images_and_backup')
                    # box.prop(scn,'mblab_remove_all_modifiers')
                    # box.prop(scn,'mblab_final_prefix')
                    # if scn.mblab_save_images_and_backup:
                    #     box.operator("mbast.finalize_character_and_images", icon='FREEZE')
                    # else:
                    #     box.operator("mbast.finalize_character", icon='FREEZE')

                if advanced_mode_is_on:
                    if gui_active_panel != "display_opt":
                        self.layout.operator('mbast.button_display_on', icon=icon_expand)
                    else:
                        self.layout.operator('mbast.button_display_off', icon=icon_collapse)
                        box = self.layout.box()

                        if mblab_humanoid.exists_displace_texture():
                            if mblab_humanoid.get_disp_visibility() == False:
                                box.operator("mbast.displacement_enable", icon='MOD_DISPLACE')
                            else:
                                box.operator("mbast.displacement_disable", icon='X')
                        if mblab_humanoid.get_subd_visibility() == False:
                            box.operator("mbast.subdivision_enable", icon='MOD_SUBSURF')
                            box.label("Subd. preview is very CPU intensive", icon='INFO')
                        else:
                            box.operator("mbast.subdivision_disable", icon='X')
                            box.label("Disable subdivision to increase the performance", icon='ERROR')
                        if mblab_humanoid.get_smooth_visibility() == False:
                            box.operator("mbast.corrective_enable", icon='MOD_SMOOTH')
                        else:
                            box.operator("mbast.corrective_disable", icon='X')

                # self.layout.operator("wellvr.take_pictures_with_camera_button", text="Take Pictures")
                self.layout.operator("wellvr.take_skin_preview_pictures_with_camera_button", text="Take SKin Preview Pics")
                # self.layout.operator('wellvr.return_to_init_screen')
                # self.layout.operator('wellvr.switch_view_button',icon='CAMERA_DATA')
                # self.layout.operator('wellvr.export_to_unreal', icon='FILE_TICK')

                if advanced_mode_is_on:
                    self.layout.label(" ")
                    self.layout.label("AFTER-CREATION TOOLS")
                    self.layout.label("After-creation tools (expressions, poses, ecc..) not available for unfinalized characters", icon="INFO")

            else:
                gui_status = "NEW_SESSION"

#EasyBastioniLAB icon & thumbnail registration
custom_icons = None # global variable to store icons in
preview_collections = {} # global variable to store thumbnails in

def register():
    from bpy.types import Scene
    from bpy.props import StringProperty, EnumProperty

    global custom_icons
    global preview_collections

    bpy.types.Scene.name_input_prop = bpy.props.StringProperty \
      (
        name = "Name input",
        description = "My description",
        default = "default"
      )

    custom_icons = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    custom_icons.load("custom_icon", os.path.join(icons_dir, "icon.png"), 'IMAGE')
    bpy.utils.register_module(__name__)

    # Generate list for skins
    pcoll_skins = bpy.utils.previews.new()
    pcoll_skins.images_location = os.path.join(os.path.dirname(__file__), "images/skin_previews")
    preview_collections["skin_previews"] = pcoll_skins
    bpy.types.Scene.skin_previews = EnumProperty(
        items=generate_skin_previews(),
        update=skin_previews_update
    )

    ### Generate lists for morph targets previews ###
    # Generate previews for Cheeks
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Cheeks_CreaseExt"] = pcoll_morphs
    bpy.types.Scene.Cheeks_CreaseExt = EnumProperty(
        items=generate_morph_previews("Cheeks_CreaseExt"),
        update=morph_previews_update_closure("Cheeks_CreaseExt")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Cheeks_InfraVolume"] = pcoll_morphs
    bpy.types.Scene.Cheeks_InfraVolume = EnumProperty(
        items=generate_morph_previews("Cheeks_InfraVolume"),
        update=morph_previews_update_closure("Cheeks_InfraVolume")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Cheeks_Mass"] = pcoll_morphs
    bpy.types.Scene.Cheeks_Mass = EnumProperty(
        items=generate_morph_previews("Cheeks_Mass"),
        update=morph_previews_update_closure("Cheeks_Mass")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Cheeks_SideCrease"] = pcoll_morphs
    bpy.types.Scene.Cheeks_SideCrease = EnumProperty(
        items=generate_morph_previews("Cheeks_SideCrease"),
        update=morph_previews_update_closure("Cheeks_SideCrease")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Cheeks_Tone"] = pcoll_morphs
    bpy.types.Scene.Cheeks_Tone = EnumProperty(
        items=generate_morph_previews("Cheeks_Tone"),
        update=morph_previews_update_closure("Cheeks_Tone")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Cheeks_Zygom"] = pcoll_morphs
    bpy.types.Scene.Cheeks_Zygom = EnumProperty(
        items=generate_morph_previews("Cheeks_Zygom"),
        update=morph_previews_update_closure("Cheeks_Zygom")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Cheeks_ZygomPosZ"] = pcoll_morphs
    bpy.types.Scene.Cheeks_ZygomPosZ = EnumProperty(
        items=generate_morph_previews("Cheeks_ZygomPosZ"),
        update=morph_previews_update_closure("Cheeks_ZygomPosZ")
    )

    # Generate previews for Chin
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Chin_Cleft"] = pcoll_morphs
    bpy.types.Scene.Chin_Cleft = EnumProperty(
        items=generate_morph_previews("Chin_Cleft"),
        update=morph_previews_update_closure("Chin_Cleft")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Chin_Prominence"] = pcoll_morphs
    bpy.types.Scene.Chin_Prominence = EnumProperty(
        items=generate_morph_previews("Chin_Prominence"),
        update=morph_previews_update_closure("Chin_Prominence")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Chin_SizeX"] = pcoll_morphs
    bpy.types.Scene.Chin_SizeX = EnumProperty(
        items=generate_morph_previews("Chin_SizeX"),
        update=morph_previews_update_closure("Chin_SizeX")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Chin_SizeZ"] = pcoll_morphs
    bpy.types.Scene.Chin_SizeZ = EnumProperty(
        items=generate_morph_previews("Chin_SizeZ"),
        update=morph_previews_update_closure("Chin_SizeZ")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Chin_Tone"] = pcoll_morphs
    bpy.types.Scene.Chin_Tone = EnumProperty(
        items=generate_morph_previews("Chin_Tone"),
        update=morph_previews_update_closure("Chin_Tone")
    )

    #Generate previews for Ears
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Ears_Lobe"] = pcoll_morphs
    bpy.types.Scene.Ears_Lobe = EnumProperty(
        items=generate_morph_previews("Ears_Lobe"),
        update=morph_previews_update_closure("Ears_Lobe")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Ears_LocY"] = pcoll_morphs
    bpy.types.Scene.Ears_LocY = EnumProperty(
        items=generate_morph_previews("Ears_LocY"),
        update=morph_previews_update_closure("Ears_LocY")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Ears_LocZ"] = pcoll_morphs
    bpy.types.Scene.Ears_LocZ = EnumProperty(
        items=generate_morph_previews("Ears_LocZ"),
        update=morph_previews_update_closure("Ears_LocZ")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Ears_RotX"] = pcoll_morphs
    bpy.types.Scene.Ears_RotX = EnumProperty(
        items=generate_morph_previews("Ears_RotX"),
        update=morph_previews_update_closure("Ears_RotX")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Ears_Round"] = pcoll_morphs
    bpy.types.Scene.Ears_Round = EnumProperty(
        items=generate_morph_previews("Ears_Round"),
        update=morph_previews_update_closure("Ears_Round")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Ears_SizeX"] = pcoll_morphs
    bpy.types.Scene.Ears_SizeX = EnumProperty(
        items=generate_morph_previews("Ears_SizeX"),
        update=morph_previews_update_closure("Ears_SizeX")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Ears_SizeY"] = pcoll_morphs
    bpy.types.Scene.Ears_SizeY = EnumProperty(
        items=generate_morph_previews("Ears_SizeY"),
        update=morph_previews_update_closure("Ears_SizeY")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Ears_SizeZ"] = pcoll_morphs
    bpy.types.Scene.Ears_SizeZ = EnumProperty(
        items=generate_morph_previews("Ears_SizeZ"),
        update=morph_previews_update_closure("Ears_SizeZ")
    )

    # Generate previews for Eyebrows
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyebrows_Angle"] = pcoll_morphs
    bpy.types.Scene.Eyebrows_Angle = EnumProperty(
        items=generate_morph_previews("Eyebrows_Angle"),
        update=morph_previews_update_closure("Eyebrows_Angle")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyebrows_Droop"] = pcoll_morphs
    bpy.types.Scene.Eyebrows_Droop = EnumProperty(
        items=generate_morph_previews("Eyebrows_Droop"),
        update=morph_previews_update_closure("Eyebrows_Droop")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyebrows_PosZ"] = pcoll_morphs
    bpy.types.Scene.Eyebrows_PosZ = EnumProperty(
        items=generate_morph_previews("Eyebrows_PosZ"),
        update=morph_previews_update_closure("Eyebrows_PosZ")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyebrows_Ridge"] = pcoll_morphs
    bpy.types.Scene.Eyebrows_Ridge = EnumProperty(
        items=generate_morph_previews("Eyebrows_Ridge"),
        update=morph_previews_update_closure("Eyebrows_Ridge")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyebrows_SizeY"] = pcoll_morphs
    bpy.types.Scene.Eyebrows_SizeY = EnumProperty(
        items=generate_morph_previews("Eyebrows_SizeY"),
        update=morph_previews_update_closure("Eyebrows_SizeY")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyebrows_Tone"] = pcoll_morphs
    bpy.types.Scene.Eyebrows_Tone = EnumProperty(
        items=generate_morph_previews("Eyebrows_Tone"),
        update=morph_previews_update_closure("Eyebrows_Tone")
    )

    # Generate previews for Eyelids
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyelids_Angle"] = pcoll_morphs
    bpy.types.Scene.Eyelids_Angle = EnumProperty(
        items=generate_morph_previews("Eyelids_Angle"),
        update=morph_previews_update_closure("Eyelids_Angle")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyelids_Crease"] = pcoll_morphs
    bpy.types.Scene.Eyelids_Crease = EnumProperty(
        items=generate_morph_previews("Eyelids_Crease"),
        update=morph_previews_update_closure("Eyelids_Crease")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyelids_InnerPosZ"] = pcoll_morphs
    bpy.types.Scene.Eyelids_InnerPosZ = EnumProperty(
        items=generate_morph_previews("Eyelids_InnerPosZ"),
        update=morph_previews_update_closure("Eyelids_InnerPosZ")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyelids_LowerCurve"] = pcoll_morphs
    bpy.types.Scene.Eyelids_LowerCurve = EnumProperty(
        items=generate_morph_previews("Eyelids_LowerCurve"),
        update=morph_previews_update_closure("Eyelids_LowerCurve")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyelids_MiddlePosZ"] = pcoll_morphs
    bpy.types.Scene.Eyelids_MiddlePosZ = EnumProperty(
        items=generate_morph_previews("Eyelids_MiddlePosZ"),
        update=morph_previews_update_closure("Eyelids_MiddlePosZ")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyelids_OuterPosZ"] = pcoll_morphs
    bpy.types.Scene.Eyelids_OuterPosZ = EnumProperty(
        items=generate_morph_previews("Eyelids_OuterPosZ"),
        update=morph_previews_update_closure("Eyelids_OuterPosZ")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyelids_SizeZ"] = pcoll_morphs
    bpy.types.Scene.Eyelids_SizeZ = EnumProperty(
        items=generate_morph_previews("Eyelids_SizeZ"),
        update=morph_previews_update_closure("Eyelids_SizeZ")
    )

    # Generate previews for Eyes
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyes_BagProminence"] = pcoll_morphs
    bpy.types.Scene.Eyes_BagProminence = EnumProperty(
        items=generate_morph_previews("Eyes_BagProminence"),
        update=morph_previews_update_closure("Eyes_BagProminence")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyes_BagSize"] = pcoll_morphs
    bpy.types.Scene.Eyes_BagSize = EnumProperty(
        items=generate_morph_previews("Eyes_BagSize"),
        update=morph_previews_update_closure("Eyes_BagSize")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyes_Crosscalibration"] = pcoll_morphs
    bpy.types.Scene.Eyes_Crosscalibration = EnumProperty(
        items=generate_morph_previews("Eyes_Crosscalibration"),
        update=morph_previews_update_closure("Eyes_Crosscalibration")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyes_InnerPosX"] = pcoll_morphs
    bpy.types.Scene.Eyes_InnerPosX = EnumProperty(
        items=generate_morph_previews("Eyes_InnerPosX"),
        update=morph_previews_update_closure("Eyes_InnerPosX")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyes_InnerPosZ"] = pcoll_morphs
    bpy.types.Scene.Eyes_InnerPosZ = EnumProperty(
        items=generate_morph_previews("Eyes_InnerPosZ"),
        update=morph_previews_update_closure("Eyes_InnerPosZ")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyes_innerSinus"] = pcoll_morphs
    bpy.types.Scene.Eyes_innerSinus = EnumProperty(
        items=generate_morph_previews("Eyes_innerSinus"),
        update=morph_previews_update_closure("Eyes_innerSinus")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyes_IrisSize"] = pcoll_morphs
    bpy.types.Scene.Eyes_IrisSize = EnumProperty(
        items=generate_morph_previews("Eyes_IrisSize"),
        update=morph_previews_update_closure("Eyes_IrisSize")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyes_OuterPosX"] = pcoll_morphs
    bpy.types.Scene.Eyes_OuterPosX = EnumProperty(
        items=generate_morph_previews("Eyes_OuterPosX"),
        update=morph_previews_update_closure("Eyes_OuterPosX")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyes_OuterPosZ"] = pcoll_morphs
    bpy.types.Scene.Eyes_OuterPosZ = EnumProperty(
        items=generate_morph_previews("Eyes_OuterPosZ"),
        update=morph_previews_update_closure("Eyes_OuterPosZ")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyes_PosX"] = pcoll_morphs
    bpy.types.Scene.Eyes_PosX = EnumProperty(
        items=generate_morph_previews("Eyes_PosX"),
        update=morph_previews_update_closure("Eyes_PosX")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyes_PosZ"] = pcoll_morphs
    bpy.types.Scene.Eyes_PosZ = EnumProperty(
        items=generate_morph_previews("Eyes_PosZ"),
        update=morph_previews_update_closure("Eyes_PosZ")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyes_Size"] = pcoll_morphs
    bpy.types.Scene.Eyes_Size = EnumProperty(
        items=generate_morph_previews("Eyes_Size"),
        update=morph_previews_update_closure("Eyes_Size")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyes_SizeZ"] = pcoll_morphs
    bpy.types.Scene.Eyes_SizeZ = EnumProperty(
        items=generate_morph_previews("Eyes_SizeZ"),
        update=morph_previews_update_closure("Eyes_SizeZ")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyes_TypeAlmond"] = pcoll_morphs
    bpy.types.Scene.Eyes_TypeAlmond = EnumProperty(
        items=generate_morph_previews("Eyes_TypeAlmond"),
        update=morph_previews_update_closure("Eyes_TypeAlmond")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Eyes_TypeHooded"] = pcoll_morphs
    bpy.types.Scene.Eyes_TypeHooded = EnumProperty(
        items=generate_morph_previews("Eyes_TypeHooded"),
        update=morph_previews_update_closure("Eyes_TypeHooded")
    )

    # Generate previews for Face
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Face_Ellipsoid"] = pcoll_morphs
    bpy.types.Scene.Face_Ellipsoid = EnumProperty(
        items=generate_morph_previews("Face_Ellipsoid"),
        update=morph_previews_update_closure("Face_Ellipsoid")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Face_Parallelepiped"] = pcoll_morphs
    bpy.types.Scene.Face_Parallelepiped = EnumProperty(
        items=generate_morph_previews("Face_Parallelepiped"),
        update=morph_previews_update_closure("Face_Parallelepiped")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Face_Triangle"] = pcoll_morphs
    bpy.types.Scene.Face_Triangle = EnumProperty(
        items=generate_morph_previews("Face_Triangle"),
        update=morph_previews_update_closure("Face_Triangle")
    )

    # Generate previews for Forehead
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Forehead_Angle"] = pcoll_morphs
    bpy.types.Scene.Forehead_Angle = EnumProperty(
        items=generate_morph_previews("Forehead_Angle"),
        update=morph_previews_update_closure("Forehead_Angle")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Forehead_Curve"] = pcoll_morphs
    bpy.types.Scene.Forehead_Curve = EnumProperty(
        items=generate_morph_previews("Forehead_Curve"),
        update=morph_previews_update_closure("Forehead_Curve")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Forehead_SizeX"] = pcoll_morphs
    bpy.types.Scene.Forehead_SizeX = EnumProperty(
        items=generate_morph_previews("Forehead_SizeX"),
        update=morph_previews_update_closure("Forehead_SizeX")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Forehead_SizeZ"] = pcoll_morphs
    bpy.types.Scene.Forehead_SizeZ = EnumProperty(
        items=generate_morph_previews("Forehead_SizeZ"),
        update=morph_previews_update_closure("Forehead_SizeZ")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Forehead_Temple"] = pcoll_morphs
    bpy.types.Scene.Forehead_Temple = EnumProperty(
        items=generate_morph_previews("Forehead_Temple"),
        update=morph_previews_update_closure("Forehead_Temple")
    )

    # Generate previews for Head
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Head_CraniumDolichocephalic"] = pcoll_morphs
    bpy.types.Scene.Head_CraniumDolichocephalic = EnumProperty(
        items=generate_morph_previews("Head_CraniumDolichocephalic"),
        update=morph_previews_update_closure("Head_CraniumDolichocephalic")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Head_CraniumPentagonoides"] = pcoll_morphs
    bpy.types.Scene.Head_CraniumPentagonoides = EnumProperty(
        items=generate_morph_previews("Head_CraniumPentagonoides"),
        update=morph_previews_update_closure("Head_CraniumPentagonoides")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Head_CraniumPlatycephalus"] = pcoll_morphs
    bpy.types.Scene.Head_CraniumPlatycephalus = EnumProperty(
        items=generate_morph_previews("Head_CraniumPlatycephalus"),
        update=morph_previews_update_closure("Head_CraniumPlatycephalus")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Head_Flat"] = pcoll_morphs
    bpy.types.Scene.Head_Flat = EnumProperty(
        items=generate_morph_previews("Head_Flat"),
        update=morph_previews_update_closure("Head_Flat")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Head_Nucha"] = pcoll_morphs
    bpy.types.Scene.Head_Nucha = EnumProperty(
        items=generate_morph_previews("Head_Nucha"),
        update=morph_previews_update_closure("Head_Nucha")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Head_Size"] = pcoll_morphs
    bpy.types.Scene.Head_Size = EnumProperty(
        items=generate_morph_previews("Head_Size"),
        update=morph_previews_update_closure("Head_Size")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Head_SizeX"] = pcoll_morphs
    bpy.types.Scene.Head_SizeX = EnumProperty(
        items=generate_morph_previews("Head_SizeX"),
        update=morph_previews_update_closure("Head_SizeX")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Head_SizeY"] = pcoll_morphs
    bpy.types.Scene.Head_SizeY = EnumProperty(
        items=generate_morph_previews("Head_SizeY"),
        update=morph_previews_update_closure("Head_SizeY")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Head_SizeZ"] = pcoll_morphs
    bpy.types.Scene.Head_SizeZ = EnumProperty(
        items=generate_morph_previews("Head_SizeZ"),
        update=morph_previews_update_closure("Head_SizeZ")
    )

    # Generate previews for Jaw
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Jaw_Angle"] = pcoll_morphs
    bpy.types.Scene.Jaw_Angle = EnumProperty(
        items=generate_morph_previews("Jaw_Angle"),
        update=morph_previews_update_closure("Jaw_Angle")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Jaw_Angle2"] = pcoll_morphs
    bpy.types.Scene.Jaw_Angle2 = EnumProperty(
        items=generate_morph_previews("Jaw_Angle2"),
        update=morph_previews_update_closure("Jaw_Angle2")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Jaw_LocY"] = pcoll_morphs
    bpy.types.Scene.Jaw_LocY = EnumProperty(
        items=generate_morph_previews("Jaw_LocY"),
        update=morph_previews_update_closure("Jaw_LocY")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Jaw_Prominence"] = pcoll_morphs
    bpy.types.Scene.Jaw_Prominence = EnumProperty(
        items=generate_morph_previews("Jaw_Prominence"),
        update=morph_previews_update_closure("Jaw_Prominence")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Jaw_ScaleX"] = pcoll_morphs
    bpy.types.Scene.Jaw_ScaleX = EnumProperty(
        items=generate_morph_previews("Jaw_ScaleX"),
        update=morph_previews_update_closure("Jaw_ScaleX")
    )

    # Generate previews for Mouth
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Mouth_CornersPosZ"] = pcoll_morphs
    bpy.types.Scene.Mouth_CornersPosZ = EnumProperty(
        items=generate_morph_previews("Mouth_CornersPosZ"),
        update=morph_previews_update_closure("Mouth_CornersPosZ")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Mouth_LowerlipExt"] = pcoll_morphs
    bpy.types.Scene.Mouth_LowerlipExt = EnumProperty(
        items=generate_morph_previews("Mouth_LowerlipExt"),
        update=morph_previews_update_closure("Mouth_LowerlipExt")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Mouth_LowerlipSizeZ"] = pcoll_morphs
    bpy.types.Scene.Mouth_LowerlipSizeZ = EnumProperty(
        items=generate_morph_previews("Mouth_LowerlipSizeZ"),
        update=morph_previews_update_closure("Mouth_LowerlipSizeZ")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Mouth_LowerlipVolume"] = pcoll_morphs
    bpy.types.Scene.Mouth_LowerlipVolume = EnumProperty(
        items=generate_morph_previews("Mouth_LowerlipVolume"),
        update=morph_previews_update_closure("Mouth_LowerlipVolume")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Mouth_PhiltrumProminence"] = pcoll_morphs
    bpy.types.Scene.Mouth_PhiltrumProminence = EnumProperty(
        items=generate_morph_previews("Mouth_PhiltrumProminence"),
        update=morph_previews_update_closure("Mouth_PhiltrumProminence")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Mouth_PhiltrumSizeX"] = pcoll_morphs
    bpy.types.Scene.Mouth_PhiltrumSizeX = EnumProperty(
        items=generate_morph_previews("Mouth_PhiltrumSizeX"),
        update=morph_previews_update_closure("Mouth_PhiltrumSizeX")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Mouth_PhiltrumSizeY"] = pcoll_morphs
    bpy.types.Scene.Mouth_PhiltrumSizeY = EnumProperty(
        items=generate_morph_previews("Mouth_PhiltrumSizeY"),
        update=morph_previews_update_closure("Mouth_PhiltrumSizeY")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Mouth_PosY"] = pcoll_morphs
    bpy.types.Scene.Mouth_PosY = EnumProperty(
        items=generate_morph_previews("Mouth_PosY"),
        update=morph_previews_update_closure("Mouth_PosY")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Mouth_PosZ"] = pcoll_morphs
    bpy.types.Scene.Mouth_PosZ = EnumProperty(
        items=generate_morph_previews("Mouth_PosZ"),
        update=morph_previews_update_closure("Mouth_PosZ")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Mouth_Protusion"] = pcoll_morphs
    bpy.types.Scene.Mouth_Protusion = EnumProperty(
        items=generate_morph_previews("Mouth_Protusion"),
        update=morph_previews_update_closure("Mouth_Protusion")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Mouth_SideCrease"] = pcoll_morphs
    bpy.types.Scene.Mouth_SideCrease = EnumProperty(
        items=generate_morph_previews("Mouth_SideCrease"),
        update=morph_previews_update_closure("Mouth_SideCrease")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Mouth_SizeX"] = pcoll_morphs
    bpy.types.Scene.Mouth_SizeX = EnumProperty(
        items=generate_morph_previews("Mouth_SizeX"),
        update=morph_previews_update_closure("Mouth_SizeX")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Mouth_UpperlipExt"] = pcoll_morphs
    bpy.types.Scene.Mouth_UpperlipExt = EnumProperty(
        items=generate_morph_previews("Mouth_UpperlipExt"),
        update=morph_previews_update_closure("Mouth_UpperlipExt")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Mouth_UpperlipSizeZ"] = pcoll_morphs
    bpy.types.Scene.Mouth_UpperlipSizeZ = EnumProperty(
        items=generate_morph_previews("Mouth_UpperlipSizeZ"),
        update=morph_previews_update_closure("Mouth_UpperlipSizeZ")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Mouth_UpperlipVolume"] = pcoll_morphs
    bpy.types.Scene.Mouth_UpperlipVolume = EnumProperty(
        items=generate_morph_previews("Mouth_UpperlipVolume"),
        update=morph_previews_update_closure("Mouth_UpperlipVolume")
    )

    # Generate previews for Nose
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Nose_BallSizeX"] = pcoll_morphs
    bpy.types.Scene.Nose_BallSizeX = EnumProperty(
        items=generate_morph_previews("Nose_BallSizeX"),
        update=morph_previews_update_closure("Nose_BallSizeX")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Nose_BasePosZ"] = pcoll_morphs
    bpy.types.Scene.Nose_BasePosZ = EnumProperty(
        items=generate_morph_previews("Nose_BasePosZ"),
        update=morph_previews_update_closure("Nose_BasePosZ")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Nose_BaseShape"] = pcoll_morphs
    bpy.types.Scene.Nose_BaseShape = EnumProperty(
        items=generate_morph_previews("Nose_BaseShape"),
        update=morph_previews_update_closure("Nose_BaseShape")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Nose_BaseSizeX"] = pcoll_morphs
    bpy.types.Scene.Nose_BaseSizeX = EnumProperty(
        items=generate_morph_previews("Nose_BaseSizeX"),
        update=morph_previews_update_closure("Nose_BaseSizeX")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Nose_BaseSizeZ"] = pcoll_morphs
    bpy.types.Scene.Nose_BaseSizeZ = EnumProperty(
        items=generate_morph_previews("Nose_BaseSizeZ"),
        update=morph_previews_update_closure("Nose_BaseSizeZ")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Nose_BridgeSizeX"] = pcoll_morphs
    bpy.types.Scene.Nose_BridgeSizeX = EnumProperty(
        items=generate_morph_previews("Nose_BridgeSizeX"),
        update=morph_previews_update_closure("Nose_BridgeSizeX")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Nose_Curve"] = pcoll_morphs
    bpy.types.Scene.Nose_Curve = EnumProperty(
        items=generate_morph_previews("Nose_Curve"),
        update=morph_previews_update_closure("Nose_Curve")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Nose_GlabellaPosZ"] = pcoll_morphs
    bpy.types.Scene.Nose_GlabellaPosZ = EnumProperty(
        items=generate_morph_previews("Nose_GlabellaPosZ"),
        update=morph_previews_update_closure("Nose_GlabellaPosZ")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Nose_GlabellaSizeX"] = pcoll_morphs
    bpy.types.Scene.Nose_GlabellaSizeX = EnumProperty(
        items=generate_morph_previews("Nose_GlabellaSizeX"),
        update=morph_previews_update_closure("Nose_GlabellaSizeX")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Nose_GlabellaSizeY"] = pcoll_morphs
    bpy.types.Scene.Nose_GlabellaSizeY = EnumProperty(
        items=generate_morph_previews("Nose_GlabellaSizeY"),
        update=morph_previews_update_closure("Nose_GlabellaSizeY")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Nose_NostrilCrease"] = pcoll_morphs
    bpy.types.Scene.Nose_NostrilCrease = EnumProperty(
        items=generate_morph_previews("Nose_NostrilCrease"),
        update=morph_previews_update_closure("Nose_NostrilCrease")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Nose_NostrilDiam"] = pcoll_morphs
    bpy.types.Scene.Nose_NostrilDiam = EnumProperty(
        items=generate_morph_previews("Nose_NostrilDiam"),
        update=morph_previews_update_closure("Nose_NostrilDiam")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Nose_NostrilPosZ"] = pcoll_morphs
    bpy.types.Scene.Nose_NostrilPosZ = EnumProperty(
        items=generate_morph_previews("Nose_NostrilPosZ"),
        update=morph_previews_update_closure("Nose_NostrilPosZ")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Nose_NostrilSizeX"] = pcoll_morphs
    bpy.types.Scene.Nose_NostrilSizeX = EnumProperty(
        items=generate_morph_previews("Nose_NostrilSizeX"),
        update=morph_previews_update_closure("Nose_NostrilSizeX")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Nose_NostrilSizeY"] = pcoll_morphs
    bpy.types.Scene.Nose_NostrilSizeY = EnumProperty(
        items=generate_morph_previews("Nose_NostrilSizeY"),
        update=morph_previews_update_closure("Nose_NostrilSizeY")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Nose_NostrilSizeZ"] = pcoll_morphs
    bpy.types.Scene.Nose_NostrilSizeZ = EnumProperty(
        items=generate_morph_previews("Nose_NostrilSizeZ"),
        update=morph_previews_update_closure("Nose_NostrilSizeZ")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Nose_PosY"] = pcoll_morphs
    bpy.types.Scene.Nose_PosY = EnumProperty(
        items=generate_morph_previews("Nose_PosY"),
        update=morph_previews_update_closure("Nose_PosY")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Nose_SeptumFlat"] = pcoll_morphs
    bpy.types.Scene.Nose_SeptumFlat = EnumProperty(
        items=generate_morph_previews("Nose_SeptumFlat"),
        update=morph_previews_update_closure("Nose_SeptumFlat")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Nose_SeptumRolled"] = pcoll_morphs
    bpy.types.Scene.Nose_SeptumRolled = EnumProperty(
        items=generate_morph_previews("Nose_SeptumRolled"),
        update=morph_previews_update_closure("Nose_SeptumRolled")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Nose_SizeY"] = pcoll_morphs
    bpy.types.Scene.Nose_SizeY = EnumProperty(
        items=generate_morph_previews("Nose_SizeY"),
        update=morph_previews_update_closure("Nose_SizeY")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Nose_TipAngle"] = pcoll_morphs
    bpy.types.Scene.Nose_TipAngle = EnumProperty(
        items=generate_morph_previews("Nose_TipAngle"),
        update=morph_previews_update_closure("Nose_TipAngle")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Nose_TipPosY"] = pcoll_morphs
    bpy.types.Scene.Nose_TipPosY = EnumProperty(
        items=generate_morph_previews("Nose_TipPosY"),
        update=morph_previews_update_closure("Nose_TipPosY")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Nose_TipPosZ"] = pcoll_morphs
    bpy.types.Scene.Nose_TipPosZ = EnumProperty(
        items=generate_morph_previews("Nose_TipPosZ"),
        update=morph_previews_update_closure("Nose_TipPosZ")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Nose_TipSize"] = pcoll_morphs
    bpy.types.Scene.Nose_TipSize = EnumProperty(
        items=generate_morph_previews("Nose_TipSize"),
        update=morph_previews_update_closure("Nose_TipSize")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Nose_WingAngle"] = pcoll_morphs
    bpy.types.Scene.Nose_WingAngle = EnumProperty(
        items=generate_morph_previews("Nose_WingAngle"),
        update=morph_previews_update_closure("Nose_WingAngle")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Nose_WingBackFlat"] = pcoll_morphs
    bpy.types.Scene.Nose_WingBackFlat = EnumProperty(
        items=generate_morph_previews("Nose_WingBackFlat"),
        update=morph_previews_update_closure("Nose_WingBackFlat")
    )
    pcoll_morphs = bpy.utils.previews.new()
    pcoll_morphs.images_location = os.path.join(os.path.dirname(__file__), "images/morph_previews")
    preview_collections["Nose_WingBump"] = pcoll_morphs
    bpy.types.Scene.Nose_WingBump = EnumProperty(
        items=generate_morph_previews("Nose_WingBump"),
        update=morph_previews_update_closure("Nose_WingBump")
    )


def unregister():
    global custom_icons
    global preview_collections


    del bpy.types.Scene.name_input_prop
    bpy.utils.previews.remove(custom_icons)

    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
    bpy.types.Scene.delete_all_properties()
    # del bpy.types.Scene.skin_previews

    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
