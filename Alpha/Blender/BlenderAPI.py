import bpy
import sys

index = int(sys.argv[-1])
import_file = sys.argv[-2]

nodes = []

for node in range(len(bpy.data.objects)):
    if bpy.data.objects[node].name != "Camera" and bpy.data.objects[node].name != "Light":
        nodes.append(bpy.data.objects[node])

for node in range(len(nodes)):
    if node != index:
        bpy.data.objects.remove(nodes[node])
        # bpy.context.collection.objects.unlink(nodes[node])

exec(import_file)
