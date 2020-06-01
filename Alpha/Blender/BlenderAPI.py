import bpy
import sys
import math


def main():
    program = sys.argv[-1]

    if program == 'Count nodes':
        nodes = 0
        for node in range(len(bpy.data.objects)):
            if bpy.data.objects[node].type == "MESH":
                nodes += 1
        print(nodes)
    elif program == 'Single node':
        exec(sys.argv[-2])
    elif program == 'Multiple nodes':
        index = int(sys.argv[-2])
        nodes = []

        node = 0
        objects = len(bpy.data.objects)
        while node < objects:
            if bpy.data.objects[node].type == "MESH":
                nodes.append(bpy.data.objects[node])
            else:
                bpy.data.objects.remove(bpy.data.objects[node])
                node -= 1
                objects -= 1
            node += 1

        for node in range(len(nodes)):
            if node != index:
                bpy.data.objects.remove(nodes[node])

        exec(sys.argv[-3])
    elif program == 'Write':
        bpy.data.objects.remove(bpy.data.objects["Cube"])

        blender_files = sys.argv[-2]
        blender_files = blender_files.split(';')

        for blender in list(filter(None, blender_files)):
            with bpy.data.libraries.load(blender) as (data_from, data_to):
                data_to.objects = data_from.objects
            for obj in data_to.objects:
                bpy.context.collection.objects.link(obj)

        exec(sys.argv[-3])

        node = 0
        objects = len(bpy.data.objects)
        while node < objects:
            if bpy.data.objects[node].type != "MESH":
                bpy.data.objects.remove(bpy.data.objects[node])
                node -= 1
                objects -= 1
            node += 1

        # angle = radian / numbers_of_ob
        A = 6.283185307179586476925286766559 / node

        # radius
        R = 50 * node

        # loop number_of_ob
        for node in range(len(bpy.data.objects)):
            if bpy.data.objects[node].type == "MESH":
                bpy.data.objects[node].location[0] = math.sin(A*node)*R       # x = sine(angle*i)*radius 
                bpy.data.objects[node].location[1] = math.cos(A*node)*R       # y = cosine(angle*i)*radius
                bpy.data.objects[node].location[2] = 0

        bpy.ops.wm.save_as_mainfile(filepath = '{}'.format(sys.argv[-4]))
    else:
        None
 

if __name__ == "__main__":
    main()
