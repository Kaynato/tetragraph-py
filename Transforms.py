import numpy as np
import math
from scipy.linalg import expm3, norm

# def rotation(theta, axis):
    # return expm3(cross(eye(3), axis/norm(axis)*theta))

def rotation(theta, axis):
    """
    Return the rotation matrix associated with counterclockwise rotation about
    the given axis by theta radians.

    http://stackoverflow.com/questions/6802577/python-rotation-of-3d-vector
    """
    axis = np.asarray(axis)
    axis = axis/math.sqrt(np.dot(axis, axis))
    a = math.cos(theta/2.0)
    b, c, d = -axis*math.sin(theta/2.0)
    aa, bb, cc, dd = a*a, b*b, c*c, d*d
    bc, ad, ac, ab, bd, cd = b*c, a*d, a*c, a*b, b*d, c*d
    return np.array([[aa+bb-cc-dd, 2*(bc+ad), 2*(bd-ac)],
                     [2*(bc-ad), aa+cc-bb-dd, 2*(cd+ab)],
                     [2*(bd+ac), 2*(cd-ab), aa+dd-bb-cc]])

def angle(angle):
	"""
	Returns angle vector.
	"""

	return np.array([math.cos(angle), math.sin(angle), 0])

def main():
	v, axis, theta = [3,5,0], [4,4,1], 1.2
	M0 = rotation(theta, axis)

	print(np.dot(M0,v))
	# [ 2.74911638  4.77180932  1.91629719]

if __name__ == '__main__':
	main()
