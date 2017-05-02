import itertools
import numpy as np


points = np.array([
	[-1.0, 0.0, 1.0],
	[ 1.0, 0.0, 1.0],
	[-1.0, 0.0,-1.0],
	[ 1.0, 0.0,-1.0],
])

camera = [-1, 1, 0]
center = [0, 0, 0]

points = np.cross(points, np.array(camera) - center)
points /= np.linalg.norm(points)

print(points)
