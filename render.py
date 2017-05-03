import sys
import itertools
import numpy as np
import Transforms

pi = 3.141592

ROTATING = True
DRAW_POSITION = False

DRAW_DELTA = True
DELTA_COLOR = [0.1, 0.1, 0.1]

MOUSE_STATE = 'up'

ALL_ATOMS = np.array(list(itertools.product([0, 1], repeat = 6))) == 1

CUBE_COLOR = [0.2, 0.1, 0.1]
STAR_COLOR = [0.1, 0.1, 0.2]

LATTICE_WIDTH = 1

TETRAD_SIZE = 0.1
TETRAD_WIDTH = 1

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

class Camera:
	def __init__(self, position, up):
		self.position = position
		self.up = up

	def rotate(self, theta, axis):
		glRotatef(theta, axis[0], axis[1], axis[2])
		rot = Transforms.rotation(-theta * pi / 180, axis)
		self.position = np.dot(rot, self.position)
		self.up = np.dot(rot, self.up)

	def orient(self):
		gluLookAt(self.position[0] * 2, self.position[1] * 2, self.position[2] * 2,
			0, 0, 0,
			self.up[0], self.up[1], self.up[2])

class Tetrad:
	def __init__(self, atoms, 
		size = TETRAD_SIZE, color = [1, 1, 1],
		point_size = 2, offset = [0, 0, 0],
		angle = 0, angle_offset = [0, 1, 0]):

		self.atoms = atoms
		self.size = size
		self.point_size = point_size
		self.color = color

		self.edges = TETRAD_EDGE_MAP[atoms]
		self.center = np.sum(TETRAD_LOCS[atoms], axis = 0)
		self.atom_count = np.sum(atoms)
		self.center = self.center / (self.atom_count + 0.001)
		self.center += offset

	def draw(self, camera):
		delta = np.array(camera.position) - self.center
		delta /= np.linalg.norm(delta)
		loc_up = camera.up - (np.dot(delta, camera.up) * delta)
		loc_up /= np.linalg.norm(loc_up)
		loc_right = np.cross(loc_up, delta)
		loc_right /= np.linalg.norm(loc_right)

		points = np.array((
			+ loc_up - loc_right,
			+ loc_up + loc_right,
			- loc_up - loc_right,
			- loc_up + loc_right
		)) * self.size / (self.atom_count + 1)

		if DRAW_DELTA:
			glBegin(GL_LINES)
			glColor3fv(DELTA_COLOR)
			glVertex3fv(self.center)
			glVertex3f(0, 0, 0)
			glEnd()

		glPointSize(self.point_size)
		glBegin(GL_POINTS)
		glColor3fv(self.color)
		for point in points:
			glVertex3fv(self.center + point)
		glEnd()

		glLineWidth(TETRAD_WIDTH)
		glBegin(GL_LINES)
		# TODO - will need to reorient to face camera
		for edge in self.edges:
			for vertex in edge:
				glVertex3fv(self.center + points[vertex])
		glEnd()

def main():
	camera = Camera(
		position = [1, 1, -2.0],
		up = [0, 1, 0]
		)

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
		glLineWidth(LATTICE_WIDTH)
		glBegin(GL_LINES)
		glColor3fv(CUBE_COLOR)
		for edge in cube_edges:
			for vertex in edge:
				glVertex3fv(CORNERS[vertex])
		glEnd()

	def Star():
		glLineWidth(LATTICE_WIDTH)
		glBegin(GL_LINES)
		glColor3fv(STAR_COLOR)
		for edge in star_edges:
			for vertex in edge:
				glVertex3fv(CORNERS[vertex])
		glEnd()

	tetrads = [
		{'draw': 1, 'states': []}, 
		{'draw': 1, 'states': []}, 
		{'draw': 1, 'states': []}, 
		{'draw': 1, 'states': []}, 
		{'draw': 1, 'states': []}, 
		{'draw': 1, 'states': []}, 
		{'draw': 1, 'states': []}, 
		{'draw': 1, 'states': []}, 
		{'draw': 1, 'states': []}, 
		{'draw': 1, 'states': []}, 
		{'draw': 1, 'states': []}
	]

	def toggle_realm(realm):
		tetrads[realm]['draw'] = (tetrads[realm]['draw'] + 1) % 3

	temp = []
	for i, atom in enumerate(ALL_ATOMS):
		atom_count = np.sum(atom)
		if atom_count == 1:
			color = [1, 1, 1]
		elif atom_count == 2:
			# red or cyan?
			color = [1, 0, 0]
		elif atom_count == 3:
			# green, magenta, or blue?
			color = [0, 1, 0]
		elif atom_count == 4:
			# lime or purple?
			color = [1, 0, 1]
		elif atom_count == 5:
			color = [0.5, 0.8, 0.8]
		elif atom_count == 6:
			color = [0, 1, 1]
		else:
			color = [0, 0, 1]
		center = np.sum(TETRAD_LOCS[atom], axis = 0)
		if (center == 0).all():
			tetrads[atom_count]['states'].append(Tetrad(atom, TETRAD_SIZE, color = color))
			
		else:
			tetrads[atom_count]['states'].append(Tetrad(atom, TETRAD_SIZE, color = color))

	#######################################################################
	#######################################################################
	#                                                                     #
	#                          RENDER / EVENTS                            #
	#                                                                     #
	#######################################################################
	#######################################################################

	def render(camera):
		global MOUSE_STATE
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				quit()

			# TODO: Might want to make a sidebar selector for real and understandable GUI though
			elif event.type == pygame.KEYDOWN:
				# only realms 1-9 are really interesting. 0, 10 are boring.
				if event.key <= 57 and event.key >= 48:
					realm = event.key - 48
					toggle_realm(realm)
				elif event.key == 65:
					toggle_realm(10)
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

				# gimbal! use "current" right and up as rotation axes

				camera.rotate(-yAngle, [0, 1, 0])
				camera.rotate(-xAngle, [1, 0, 0])

		rotating = MOUSE_STATE == 'up'

		if rotating:
			camera.rotate(1, [1, 2, 3])

		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

		# TODO: Render the appropriate lattices?
		Cube()
		Star()

		for realm in tetrads:
			if realm['draw']:
				for tetrad in realm['states']:
					tetrad.draw(camera)

		if DRAW_POSITION:
			glPointSize(5)
			glBegin(GL_POINTS)
			glVertex3fv(POSITION)
			glEnd()

		pygame.display.flip()
		pygame.time.wait(10)

	pygame.init()

	display = [640, 480]

	screen = pygame.display.set_mode(display, DOUBLEBUF|OPENGL)

	gluPerspective(20.0, (display[0]/display[1]), 0.1, 50.0)

	camera.orient()
	
	while True:
		render(camera)

if __name__ == '__main__':
	main()
