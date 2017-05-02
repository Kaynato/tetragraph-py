import sys
import itertools
import numpy as np
import Transforms

pi = 3.141592

GLOBAL_UP = [0, 1, 0]
POSITION = np.array([0, 0, -4.0])

MOUSE_STATE = 'up'

ALL_ATOMS = np.array(list(itertools.product([0, 1], repeat = 6))) == 1

CUBE_COLOR = [0.2, 0.1, 0.1]
STAR_COLOR = [0.1, 0.1, 0.2]

TETRAD_SIZE = 0.1

# Edges corresponding to the bases
TETRAD_EDGE_MAP = np.array([
	[0, 1], # F / vapor - white
	[0, 3], # U / water - blue
	[1, 3], # R / stone - yellow
	[0, 2], # L / flame - red
	[1, 2], # D / earth - green
	[2, 3]  # B / metal - black
])

# Locations of the bases
TETRAD_LOCS = np.array([
	[ 0, 0, 1], # F / vapor - white
	[ 0, 1, 0], # U / water - blue
	[ 1, 0, 0], # R / stone - yellow
	[-1, 0, 0], # L / flame - red
	[ 0,-1, 0], # D / earth - green
	[ 0, 0,-1]  # B / metal - black
])

TETRAD_BASES = np.identity(6)

x = np.linspace(-1, 1, 2)
CORNERS = np.array(np.meshgrid(x, x, x)).T.reshape(8,3)
del x

import pygame
import OpenGL

from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

def main():
	cube_edges = []
	star_edges = []

	# definitely can be made parallel, but for now...
	for i in np.r_[0:len(CORNERS)]:
		for j in np.r_[i:len(CORNERS)]:
			if np.sum(CORNERS[i] == CORNERS[j]) == 2:
				if len(cube_edges) == 0:
					cube_edges = [[i, j]]
				else:
					cube_edges = np.append(cube_edges[:], [[i, j]], axis=0)
			elif np.sum(CORNERS[i] == CORNERS[j]) == 1:
				if len(star_edges) == 0:
					star_edges = [[i, j]]
				else:
					star_edges = np.append(star_edges[:], [[i, j]], axis=0)

	def Cube():
		glBegin(GL_LINES)
		glColor3fv(CUBE_COLOR)
		for edge in cube_edges:
			for vertex in edge:
				glVertex3fv(CORNERS[vertex])
		glEnd()

	def Star():
		glBegin(GL_LINES)
		glColor3fv(STAR_COLOR)
		for edge in star_edges:
			for vertex in edge:
				glVertex3fv(CORNERS[vertex])
		glEnd()

	def i_Tetrad(atoms, size, color = [1, 1, 1], point_size = 2, offset = [0, 0, 0]):
		# glBegin(GL_TRIANGLE_FAN);

		locs = TETRAD_LOCS[atoms]
		atom_count = np.sum(atoms)
		center = np.sum(locs, axis = 0)
		edges = TETRAD_EDGE_MAP[atoms]
		center = center / (atom_count + 0.001)

		# points = np.array([
		# 	[-1.0, 0.0, 1.0],
		# 	[ 1.0, 0.0, 1.0],
		# 	[-1.0, 0.0,-1.0],
		# 	[ 1.0, 0.0,-1.0],
		# ])

		# points *= size / (atom_count + 0.001)

		def draw_tetrad(): # also rotation?
			global POSITION

			glPointSize(point_size)
			glBegin(GL_POINTS)
			glColor3fv(color)

			delta = np.array(POSITION) - center
			delta /= np.linalg.norm(delta)

			loc_up = GLOBAL_UP - np.dot(delta, GLOBAL_UP)
			loc_up *= size / ((atom_count + 0.001) * np.linalg.norm(loc_up))

			loc_right = np.cross(loc_up, delta)

			points = np.array((
				+ loc_up - loc_right,
				+ loc_up + loc_right,
				- loc_up - loc_right,
				- loc_up + loc_right
			))

			for point in points:
				glVertex3fv(offset + center + point)
			glEnd()

			glBegin(GL_LINES)
			# TODO - will need to reorient to face camera
			for edge in edges:
				for vertex in edge:
					point = center + points[vertex]
					glVertex3fv(point)
			glEnd()

		return draw_tetrad

	tetrads = []

	for atom in ALL_ATOMS:
		tetrads.append(i_Tetrad(atom, TETRAD_SIZE))


	#######################################################################
	#######################################################################
	#                                                                     #
	#                               RENDER                                #
	#                                                                     #
	#######################################################################
	#######################################################################

	def render():
		global MOUSE_STATE, POSITION

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				quit()

			elif event.type == pygame.MOUSEBUTTONDOWN and MOUSE_STATE == 'up':
				if event.button == 1:
					pygame.mouse.get_rel()
					MOUSE_STATE = 'down'

			elif event.type == pygame.MOUSEBUTTONUP:
				if event.button == 1 and MOUSE_STATE == 'down':
					pygame.mouse.get_rel()
					MOUSE_STATE = 'up'
				elif event.button == 4:
					glScalef(1.1, 1.1, 1.1)
				elif event.button == 5:
					glScalef(1/1.1, 1/1.1, 1/1.1)

			elif event.type == pygame.MOUSEMOTION and MOUSE_STATE == 'down':
				xAngle, yAngle = pygame.mouse.get_rel()

				# POSITION[0] += xAngle / 100
				# POSITION[1] -= yAngle / 100

				# glTranslatef(0, -yAngle / 100, 0)
				# glTranslatef(xAngle / 100, 0, 0)
				glRotatef(-yAngle, 0, 1, 0)
				yRot = Transforms.rotation(-yAngle * pi / 180, [0, 1, 0])
				glRotatef(-xAngle, 1, 0, 0)
				xRot = Transforms.rotation(-xAngle * pi / 180, [1, 0, 0])

				POSITION = np.dot(xRot, np.dot(yRot, POSITION))

				print(POSITION)

				# gluLookAt(POSITION[0], POSITION[1], POSITION[2],
					# 0, 0, 0,
					# 0, 1, 0)


		glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
		Cube()
		Star()
		for draw_tetrad in tetrads:
			draw_tetrad()
		pygame.display.flip()
		pygame.time.wait(10)

	pygame.init()

	display = [640, 480]

	# POSITION = [-1.0, -4.0, -1.0]
	# locations = np.tile(CORNERS, (1, 1))
	# look = POSITION - locations
	# local_up = [0, 0, 1]
	# local_right = np.cross(local_up, look)
	# local_look = np.cross(local_right, local_up)

	screen = pygame.display.set_mode(display, DOUBLEBUF|OPENGL)
	gluPerspective(45, (display[0]/display[1]), 0.1, 50.0)
	glTranslatef(POSITION[0], POSITION[1], POSITION[2])

	# gluLookAt(POSITION[0], POSITION[1], POSITION[2],
		# 0, 0, 0,
		# 0, 1, 0)

	while True:
		render()

if __name__ == '__main__':
	main()
