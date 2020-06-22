# Imports from the python standard library.
import sys
import math
import os

# Imports from the blender python library.
import bpy


## Removes the entire scene.
def removeScene():
    node = 0
    objects = len(bpy.context.collection.objects)
    while node < objects:
        bpy.context.collection.objects.unlink(bpy.context.collection.objects[node])
        objects -= 1


##  Loads the given .blend file as a library.
#
#   \param file_path  The path of the .blend file.
#   \return           All real objects without any decorators.
def loadLibrary(file_path):
    with bpy.data.libraries.load(file_path) as (src, dst):
        dst.objects = src.objects
    removeDecorators(dst.objects, 'library')
    return dst.objects
    

##  Removes all decorators (Camera, Light, ...).
#
#   \param objects  A list of objects.
#   \param library  Flag that indicates a library. For compatibility reasons.
def removeDecorators(objects, library = None):
    node = 0
    nodes = len(objects)
    while node < nodes:
        if objects[node].type != "MESH":
            if library:
                objects.remove(objects[node])
            else:
                objects.unlink(objects[node])
            node -= 1
            nodes -= 1
        node += 1


##  Finds the object with the given index and links it to the scene.
#
#   \param objects    A list of objects.
#   \param index      The index of the object. Used for files with multiple objects.
#   \param file_path  The file path for renaming purpose. Used in 'Write' mode.
def findIndexAndLink(objects, index, file_path = None):
    for node in range(len(objects)):
        if node == index:
            if file_path:
                objects[node].name = '{}_{}_NEW'.format(os.path.basename(file_path).rsplit('.', 1)[0], os.path.basename(file_path).rsplit('.', 1)[-1])
            bpy.context.collection.objects.link(objects[node])


##  Repositions all objects in the blender file along the x-axis. Used in 'Write' mode.
def repositionObjects():
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


##  Main program. 
def main():
    program = sys.argv[-1]

    # Program for counting nodes inside a file.
    if program == 'Count nodes':
        nodes = 0
        for node in range(len(bpy.context.collection.objects)):
            if bpy.context.collection.objects[node].type == "MESH":
                nodes += 1
        print(nodes)
    # Program for loading files with a single node.
    elif program == 'Single node':
        removeDecorators(bpy.context.collection.objects)
        exec(sys.argv[-2])
    # Program for loading files with multiple nodes.
    elif program == 'Multiple nodes':
        file_path = sys.argv[-2]
        index = int(sys.argv[-3])

        removeScene()
        
        objects = loadLibrary(file_path)
        
        findIndexAndLink(objects, index)

        exec(sys.argv[-4])
    # Program for creating a file.
    elif program == 'Write':
        blender_files = sys.argv[-2]
        blender_files = blender_files.split(';')
        
        removeScene()
        # Process blender files.
        for file_path in list(filter(None, blender_files)):
            if '_curasplit_' in file_path:
                index = int(file_path[file_path.index('_curasplit_') + 11:][:-6]) - 1
                original_path = '{}.blend'.format(file_path[:file_path.index('_curasplit_')])

                objects = loadLibrary(original_path)

                findIndexAndLink(objects, index, file_path)

            else:
                objects = loadLibrary(file_path)
                
                for node in objects:
                    node.name = '{}_{}_NEW'.format(os.path.basename(file_path).strip('.blend'), os.path.basename(file_path).rsplit('.', 1)[-1])
                    bpy.context.collection.objects.link(node)

        execute_list = sys.argv[-3]
        execute_list = execute_list.split(';')
        # Process foreign files.
        for execute in list(filter(None, execute_list)):
            exec(execute)
            for node in bpy.context.collection.objects:
                if not node.name.endswith('_NEW'):
                    file_name = os.path.basename(execute[execute.index('filepath = ') + 12:][:-2])
                    node.name = '{}_{}_NEW'.format(file_name.rsplit('.', 1)[0], file_name.rsplit('.', 1)[-1])

        # Reposition all objects.
        repositionObjects()

        # Save the file on given filepath.
        bpy.ops.wm.save_as_mainfile(filepath = '{}'.format(sys.argv[-4]))

    # Wrong program call.
    else:
        None


##  Main entry point that calls the program.
if __name__ == "__main__":
    main()
