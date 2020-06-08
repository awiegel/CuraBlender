import bpy
import sys
import math
import os


def removeScene():
    node = 0
    objects = len(bpy.context.collection.objects)
    while node < objects:
        bpy.context.collection.objects.unlink(bpy.context.collection.objects[node])
        objects -= 1


def loadLibrary(file_path):
    with bpy.data.libraries.load(file_path) as (src, dst):
        dst.objects = src.objects
    removeDecorators(dst.objects, 'library')
    return dst.objects
    

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


def findIndexAndLink(objects, index, file_path = None):
    for node in range(len(objects)):
        if node == index:
            if file_path:
                objects[node].name = '{}_{}_NEW'.format(os.path.basename(file_path).rsplit('.', 1)[0], os.path.basename(file_path).rsplit('.', 1)[-1])
            bpy.context.collection.objects.link(objects[node])


def repositionObjects():
    # angle = radian / numbers_of_ob
    A = 6.283185307179586476925286766559 / len(bpy.context.collection.objects)

    #dimensions = (0, 0, 0)
    #for node in bpy.context.collection.objects:
    #    dimensions += bpy.context.collection.objects[node].dimensions
    #dimensions /= len(bpy.context.collection.objects)

    # radius
    R = 50 * len(bpy.context.collection.objects)

    # loop number_of_ob
    for node in range(len(bpy.context.collection.objects)):
        if bpy.context.collection.objects[node].type == "MESH":
            bpy.context.collection.objects[node].location[0] = math.sin(A*node)*R       # x = sine(angle*i)*radius 
            bpy.context.collection.objects[node].location[1] = math.cos(A*node)*R       # y = cosine(angle*i)*radius
            bpy.context.collection.objects[node].location[2] = 0


def main():
    program = sys.argv[-1]

    if program == 'Count nodes':
        nodes = 0
        for node in range(len(bpy.context.collection.objects)):
            if bpy.context.collection.objects[node].type == "MESH":
                nodes += 1
        print(nodes)

    elif program == 'Single node':
        removeDecorators(bpy.context.collection.objects)
        exec(sys.argv[-2])

    elif program == 'Multiple nodes':
        file_path = sys.argv[-2]
        index = int(sys.argv[-3])

        removeScene()
        
        objects = loadLibrary(file_path)
        
        findIndexAndLink(objects, index)

        exec(sys.argv[-4])

    elif program == 'Write':
        blender_files = sys.argv[-2]
        blender_files = blender_files.split(';')
        
        removeScene()

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
        for execute in list(filter(None, execute_list)):
            exec(execute)
            for node in bpy.context.collection.objects:
                if not node.name.endswith('_NEW'):
                    file_name = os.path.basename(execute[execute.index('filepath = ') + 12:][:-2])
                    node.name = '{}_{}_NEW'.format(file_name.rsplit('.', 1)[0], file_name.rsplit('.', 1)[-1])

        repositionObjects()

        bpy.ops.wm.save_as_mainfile(filepath = '{}'.format(sys.argv[-4]))

    else:
        None
 

if __name__ == "__main__":
    main()
