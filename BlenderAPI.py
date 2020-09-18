# Imports from the python standard library.
import sys
import math
import os

# Imports from the blender python library.
import bpy


def removeScene():
    """Removes the entire scene."""

    node = 0
    objects = len(bpy.context.collection.objects)
    while node < objects:
        bpy.context.collection.objects.unlink(bpy.context.collection.objects[node])
        objects -= 1


def loadLibrary(file_path):
    """Loads the given .blend file as a library.

    :param file_path: The path of the .blend file.
    :return: All real objects without any decorators.
    """

    with bpy.data.libraries.load(file_path) as (src, dst):
        dst.objects = src.objects
    return dst.objects
    

def removeDecorators(objects):
    """Removes all decorators (Camera, Light, ...).

    :param objects: A list of objects.
    """

    node = 0
    nodes = len(objects)
    while node < nodes:
        if objects[node].type != "MESH":
            objects.remove(objects[node])
            node -= 1
            nodes -= 1
        node += 1


def removeInactiveObjects(objects):
    """Removes all inactive objects (hide or exclude from viewport).

    :param objects: A list of objects.
    """

    for collection in range(len(bpy.data.collections)):
        node = 0
        nodes = len(bpy.data.collections[collection].objects)
        while node < nodes:
            data = bpy.data.collections[collection].objects[node]
            if not data.visible_get():
                objects.remove(data)
                node -= 1
                nodes -= 1
            node += 1


def linkAndRenameObjects(objects, file_path):
    """Renames and links all objects to the scene.

    :param objects: A list of objects.
    :param file_path: The file path for renaming purpose. Used in 'Write' mode.
    """

    for node in range(len(objects)):
        objects[node].name = '{}_{}_NEW'.format(os.path.basename(file_path).rsplit('.', 1)[0], os.path.basename(file_path).rsplit('.', 1)[-1])
        bpy.context.collection.objects.link(objects[node])


def findIndexAndRemoveOtherObjects(objects, index):
    """Finds the object with the given index and removes all other objects from the scene.

    :param objects: A list of objects.
    :param index: The index of the object. Used for files with multiple objects.
    """

    node = 0
    nodes = len(objects)
    while node < nodes:
        if node != index:
            objects.remove(objects[node])
            node -= 1
            nodes-= 1
            index -= 1
        node += 1


def repositionObjects():
    """Repositions all objects in the blender file along the x-axis. Used in 'Write' mode."""

    # Calculates the average distance between nodes.
    distance = 0
    for node in range(len(bpy.context.collection.objects)):
        distance += bpy.context.collection.objects[node].dimensions[0]
    distance /= 10

    for node in range(len(bpy.context.collection.objects)):
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
        removeInactiveObjects(bpy.data.objects)
        nodes = 0
        for node in range(len(bpy.data.objects)):
            if bpy.data.objects[node].type == "MESH":
                nodes += 1
        print(nodes)

    # Program for loading files with a single node.
    elif program == 'Single node':
        removeDecorators(bpy.data.objects)
        removeInactiveObjects(bpy.data.objects)
        exec(sys.argv[-2])

    # Program for loading files with multiple nodes.
    elif program == 'Multiple nodes':
        index = int(sys.argv[-2])

        removeDecorators(bpy.data.objects)
        removeInactiveObjects(bpy.data.objects)

        findIndexAndRemoveOtherObjects(bpy.data.objects, index)

        exec(sys.argv[-3])

    # Program for preparing the 'Write' step.
    elif program == 'Write prepare':
        removeDecorators(bpy.data.objects)
        removeInactiveObjects(bpy.data.objects)
        bpy.ops.wm.save_as_mainfile(filepath = '{}'.format(sys.argv[-2]))

    # Program for creating a file.
    elif program == 'Write':
        removeScene()

        blender_files = sys.argv[-2]
        blender_files = blender_files.split(';')
        # Processes blender files.
        for file_path in list(filter(None, blender_files)):
            objects = loadLibrary(file_path)
            linkAndRenameObjects(objects, file_path)
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
        repositionObjects()

        # Saves the file on given filepath.
        bpy.ops.wm.save_as_mainfile(filepath = '{}'.format(sys.argv[-4]))

    # Wrong program call.
    else:
        None


if __name__ == "__main__":
    """Main entry point that calls the program."""

    main()
