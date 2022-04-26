"""Interface to Blender."""

# Imports from the python standard library.
import sys
import os

# Imports from the blender python library.
import bpy


def remove_scene():
    """Removes the entire scene."""

    node = 0
    objects = len(bpy.context.collection.objects)
    while node < objects:
        bpy.context.collection.objects.unlink(bpy.context.collection.objects[node])
        objects -= 1


def load_library(file_path):
    """Loads the given .blend file as a library.

    :param file_path: The path of the .blend file.
    :return: All real objects without any decorators.
    """

    with bpy.data.libraries.load(file_path) as (src, dst):
        dst.objects = src.objects
    return dst.objects


def remove_decorators(objects):
    """Removes all decorators (Camera, Light, ...).

    :param objects: A list of objects.
    """

    node = 0
    nodes = len(objects)
    while node < nodes:
        if objects[node].type != "MESH":
            objects.remove(objects[node])
            nodes -= 1
        else:
            node += 1


def remove_inactive_objects(objects):
    """Removes all inactive objects (hide or exclude from viewport).

    :param objects: A list of objects.
    """

    for collection, _ in enumerate(bpy.data.collections):
        node = 0
        nodes = len(bpy.data.collections[collection].objects)
        while node < nodes:
            data = bpy.data.collections[collection].objects[node]
            if not data.visible_get():
                objects.remove(data)
                nodes -= 1
            else:
                node += 1


def link_and_rename_objects(objects, file_path):
    """Renames and links all objects to the scene.

    :param objects: A list of objects.
    :param file_path: The file path for renaming purpose. Used in 'Write' mode.
    """

    for node, _ in enumerate(objects):
        objects[node].name = '{}_{}_NEW'.format(os.path.basename(file_path).rsplit('.', 1)[0], os.path.basename(file_path).rsplit('.', 1)[-1])
        bpy.context.collection.objects.link(objects[node])


def find_index_and_remove_other_objects(objects, index):
    """Finds the object with the given index and removes all other objects from the scene.

    :param objects: A list of objects.
    :param index: The index of the object. Used for files with multiple objects.
    """

    node = 0
    nodes = len(objects)
    while node < nodes:
        if node != index:
            objects.remove(objects[node])
            nodes-= 1
            index -= 1
        else:
            node += 1


def reposition_objects():
    """Repositions all objects in the blender file along the x-axis. Used in 'Write' mode."""

    # Calculates the average distance between nodes.
    distance = 0
    for node, _ in enumerate(bpy.context.collection.objects):
        distance += bpy.context.collection.objects[node].dimensions[0]
    distance /= 10

    for node, _ in enumerate(bpy.context.collection.objects):
        # Positions first node.
        if node == 0:
            bpy.context.collection.objects[node].location[0] = 0
            bpy.context.collection.objects[node].location[1] = 0
            bpy.context.collection.objects[node].location[2] = 0
            length = (bpy.context.collection.objects[node].dimensions[0] / 2) + distance
        # Positions every other node.
        else:
            bpy.context.collection.objects[node].location[0] = length + (bpy.context.collection.objects[node].dimensions[0] / 2)
            bpy.context.collection.objects[node].location[1] = 0
            bpy.context.collection.objects[node].location[2] = 0
            length += bpy.context.collection.objects[node].dimensions[0] + distance


def main():
    """Main program."""

    program = sys.argv[-1]

    # Program for counting nodes inside a file.
    if program == 'Count nodes':
        remove_inactive_objects(bpy.data.objects)
        nodes = 0
        for node, _ in enumerate(bpy.data.objects):
            if bpy.data.objects[node].type == "MESH":
                nodes += 1
        print(nodes)

    # Program for loading files with a single node.
    elif program == 'Single node':
        remove_decorators(bpy.data.objects)
        remove_inactive_objects(bpy.data.objects)
        exec(sys.argv[-2])

    # Program for loading files with multiple nodes.
    elif program == 'Multiple nodes':
        index = int(sys.argv[-2])

        remove_decorators(bpy.data.objects)
        remove_inactive_objects(bpy.data.objects)

        find_index_and_remove_other_objects(bpy.data.objects, index)

        exec(sys.argv[-3])

    # Program for preparing the 'Write' step.
    elif program == 'Write prepare':
        remove_decorators(bpy.data.objects)
        remove_inactive_objects(bpy.data.objects)
        bpy.ops.wm.save_as_mainfile(filepath = '{}'.format(sys.argv[-2]))

    # Program for creating a file.
    elif program == 'Write':
        remove_scene()

        blender_files = sys.argv[-2]
        blender_files = blender_files.split(';')
        # Processes blender files.
        for file_path in list(filter(None, blender_files)):
            objects = load_library(file_path)
            link_and_rename_objects(objects, file_path)
            os.remove(file_path)

        execute_list = sys.argv[-3]
        execute_list = execute_list.split(';')
        # Processes foreign files.
        for execute in list(filter(None, execute_list)):
            exec(execute)
            for node in bpy.context.collection.objects:
                if not node.name.endswith('_NEW'):
                    file_name = os.path.basename(execute[execute.index('filepath = ') + 12:][:-2])
                    node.name = '{}_{}_NEW'.format(file_name.rsplit('.', 1)[0], file_name.rsplit('.', 1)[-1])

        # Repositions all objects.
        reposition_objects()

        # Saves the file on given filepath.
        bpy.ops.wm.save_as_mainfile(filepath = '{}'.format(sys.argv[-4]))

    # Wrong program call.
    else:
        pass


if __name__ == "__main__":
    main()
