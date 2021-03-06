import sys
import itertools
import numpy as np
import Transforms

DRAW_POSITION = False

DRAW_DELTA = False
DELTA_COLOR = [0.1, 0.1, 0.1]

ALL_ATOMS = np.array(list(itertools.product([0, 1], repeat = 6))) == 1

LATTICE_WIDTH = 1
LATTICE_COLORMOD = 0.35

TETRAD_SIZE = 0.1
TETRAD_WIDTH = 1

# Edges corresponding to the bases' values
# Consider also other orderings
TETRAD_EDGE_MAP = np.array([
	[0, 1], # U / vapor - white
	[0, 3], # F / water - blue
	[1, 3], # R / stone - yellow
	[0, 2], # L / flame - red
	[1, 2], # B / earth - green
	[2, 3]  # D / metal - black
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

REALM_COLORS = np.array([
	[0.0, 0.0, 0.0], # 0 black
	[1.0, 1.0, 1.0], # 1 white
	[1.0, 0.0, 0.0], # 2 red
	[0.0, 1.0, 1.0], # 3 cyan
	[0.0, 0.0, 1.0], # 4 blue
	[1.0, 0.0, 1.0], # 5 magenta
	[0.0, 1.0, 0.0], # 6 green
	[0.5, 0.8, 1.0], # 7 lime (??)
	[0.4, 0.0, 0.8], # 8 purple (dark)
	[0.8, 0.4, 0.0], # 9 orange
	[1.0, 1.0, 0.0], # F gold
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

class Camera(object):
	slider_rate = 0.01
	spin_rate = 0.1

	def __init__(self, position, up):
		self.position = np.array(position)
		self.up = up
		self.aspeed = 0.1
		self.moment = np.array([0, 1, 0])

		self._slider = 0
		self.mscale = 1
		self.theta = 0

	def rotate(self, theta, axis):
		if not axis.any():
			return
		glRotatef(theta, axis[0], axis[1], axis[2])
		rot = Transforms.rotation(-np.deg2rad(theta), axis)
		self.position = np.dot(rot, self.position)
		self.up = np.dot(rot, self.up)
		self.theta += Camera.spin_rate * theta
		if self.theta > 16 * np.pi:
			self.theta -= 16 * np.pi

	def spin(self):
		theta = self.theta
		return np.sin(np.array([theta + np.pi/3, 2 * theta + 2*np.pi/3, 3 * theta + np.pi, 0, 0, 0]))

	def scale(self, sigma):
		glScalef(sigma, sigma, sigma)
		# self.position = self.position * sigma

	def orient(self):
		gluLookAt(self.position[0], self.position[1], self.position[2],
			0, 0, 0,
			self.up[0], self.up[1], self.up[2])

	@property
	def right(self):
		right = np.cross(self.up, -self.position)
		return right / np.linalg.norm(right)

	@property
	def mscale(self):
		return (np.cos(np.pi * self.slider) + 1) / 2.0

	@mscale.setter
	def mscale(self, value):
		self._mscale = value

	@property
	def slider(self):
		return self._slider

	@slider.setter
	def slider(self, value):
		if value > 1:
			self._slider = 1
		elif value < 0:
			self._slider = 0
		else:
			self._slider = value

	def set_screen(self, display):
		self.screen = pygame.display.set_mode(display, DOUBLEBUF|OPENGL|pygame.RESIZABLE)
		gluPerspective(20.0, (display[0]/display[1]), 0.1, 50.0)

	def idle(self):
		self.rotate(self.aspeed, self.moment)

class Actives:
	def __init__(self):
		self.items = {}

	def has(self, item):
		self.items[item] = self.items.get(item, False)
		return self.items[item]

	def on(self, item):
		self.items[item] = True

	def off(self, item):
		self.items[item] = False

class Tetrad:
	null_realms = [3, 7]
	realm3 = np.array([33, 18, 12])
	realm4 = np.array([11, 21, 38, 56])
	realm6 = 63 - realm4
	realm7 = 63 - realm3

	def __init__(self, atoms, value, size = TETRAD_SIZE, point_size = 2):
		self.atoms = atoms
		self.value = value
		self.size = size
		self.point_size = point_size
		self.color = color

		self.edges = TETRAD_EDGE_MAP[atoms]
		self.atom_count = np.sum(atoms)

		self.location = np.sum(TETRAD_LOCS[atoms], axis = 0)

		self.center = self.location / (self.atom_count + 0.001)

		if self.atom_count < 2:
			self.realm = self.atom_count
		elif self.atom_count > 4:
			self.realm = self.atom_count + 4
		elif self.atom_count == 2:
			if value in Tetrad.realm3:
				self.realm = 3
			else:
				self.realm = 2
		elif self.atom_count == 3:
			if value in Tetrad.realm4:
				self.realm = 4
			elif value in Tetrad.realm6:
				self.realm = 6
			else:
				self.realm = 5
		elif self.atom_count == 4:
			if value in Tetrad.realm7:
				self.realm = 7
			else:
				self.realm = 8

		self.color = REALM_COLORS[self.realm]

	def draw(self, camera):
		if self.atom_count == 0:
			self.center = [0, 0, 0]
		elif self.realm not in Tetrad.null_realms or camera.slider == 0:
			self.center = self.location / (self.atom_count ** camera.mscale + 0.001)
		else:
			basis = self.atoms * camera.spin()
			basis *= 1 if self.realm == 3 else -1
			self.center = np.sum(TETRAD_LOCS * basis[:, np.newaxis], axis=0)
			# normalizing unfortunately screws up the symmetry
			# if self.realm == 7:
				# self.center /= np.linalg.norm(self.center)
			# self.center /= (self.atom_count ** camera.mscale + 0.001)
			self.center /= (self.atom_count + 0.001)
			self.center *= 1 - camera.mscale

		delta = 5 * np.array(camera.position) - self.center
		delta = delta / np.linalg.norm(delta)

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
			glVertex3fv(camera.position)
			# glVertex3f(0, 0, 0)
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

class Lattice:
	no_cross = True

	def __init__(self, realm, states):
		"""
		Take in a list of tetrads, and make a lattice on the ones that differ by 'diff'
		Our color is the average of their colors.
		"""
		self.realm = realm
		self.states = states
		edges = []

		# get all edges except for the ones that go through the center (if cross is false)
		for i in np.r_[0:len(states)]:
			for j in np.r_[i:len(states)]:
				# TODO toggle "transformation edges?"
				# edges of transformation by the 3 primal transformations?

				# avoid center crossing if cross is false
				crossed = not (states[i].center + states[j].center).any()

				if not (Lattice.no_cross and crossed) or realm in Tetrad.null_realms:
					if realm != 8 and realm != 2:
						edges.append([i, j])
					else:
						# xor can't be within realm 2
						intsc = sum(states[i].atoms * states[j].atoms)
						valsc = states[i].value ^ states[j].value
						if realm == 2 and intsc == 1 and valsc not in Tetrad.realm3:
							edges.append([i, j])
						if realm == 8 and intsc == 3 and valsc not in Tetrad.realm3:
							edges.append([i, j])

		self.edges = edges
		self.color = REALM_COLORS[realm] * LATTICE_COLORMOD

	def draw(self):
		# return if self.realm in Tetrad.null_realms
		glLineWidth(LATTICE_WIDTH)
		glBegin(GL_LINES)
		glColor3fv(self.color)
		for edge in self.edges:
			for vertex in edge:
				glVertex3fv(self.states[vertex].center)
		glEnd()

def main():
	camera = Camera(
		position = [1, 1, 0],
		up = [0, 1, 0]
	)

	actives = Actives()

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

	for i, atom in enumerate(ALL_ATOMS):
		tetrad = Tetrad(atom, i, TETRAD_SIZE)
		tetrads[tetrad.realm]['states'].append(tetrad)

	for i, realm in enumerate(tetrads):
		realm['lattice'] = Lattice(i, realm['states'])

	#######################################################################
	#######################################################################
	#                                                                     #
	#                            LOOP / EVENTS                            #
	#                                                                     #
	#######################################################################
	#######################################################################

	def loop(camera, actives):
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
				else:
					print(pygame.key.name(event.key), 'down')
					if not actives.has(event.key):
						actives.on(event.key)

			elif event.type == pygame.KEYUP:
				if (event.key > 57 and event.key != 65) or event.key < 48:
					print(pygame.key.name(event.key), 'up')
					if actives.has(event.key):
						actives.off(event.key)

			elif event.type == pygame.MOUSEBUTTONDOWN and not actives.has('mouse'):
				if event.button == 1:
					pygame.mouse.get_rel()
					actives.on('mouse')

			elif event.type == pygame.MOUSEBUTTONUP:
				if event.button == 1 and actives.has('mouse'):
					pygame.mouse.get_rel()
					actives.off('mouse')
				elif event.button == 4:
					camera.scale(1.1)
				elif event.button == 5:
					camera.scale(1/1.1)

			elif event.type == pygame.MOUSEMOTION and actives.has('mouse'):
				xAngle, yAngle = pygame.mouse.get_rel()
				camera.rotate(-yAngle, camera.right)
				camera.rotate(+xAngle, camera.up)

				camera.aspeed = (xAngle + yAngle) / 8.0
				camera.moment = xAngle * camera.up - yAngle * camera.right

			elif event.type == VIDEORESIZE:
				# The main code that resizes the window:
				camera.set_screen([event.w, event.h])
				camera.orient()

		rotating = not actives.has('mouse')
		if rotating:
			camera.idle()

		# up and down arrow keys to control slider
		if actives.has(pygame.K_UP):
			camera.slider += Camera.slider_rate
		if actives.has(pygame.K_DOWN):
			camera.slider -= Camera.slider_rate

		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

		for realm in tetrads:
			# draw at all
			if realm['draw'] > 1:
				realm['lattice'].draw()
			if realm['draw']:
				for tetrad in realm['states']:
					tetrad.draw(camera)
			# draw lattice if at least 2

		if DRAW_POSITION:
			glPointSize(5)
			glBegin(GL_POINTS)
			glVertex3fv(camera.position)
			glEnd()

		pygame.display.flip()
		pygame.time.wait(10)

	pygame.init()

	camera.set_screen([640, 480])
	camera.orient()
	
	while True:
		loop(camera, actives)

if __name__ == '__main__':
	main()
