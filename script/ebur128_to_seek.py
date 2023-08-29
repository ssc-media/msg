#! /usr/bin/python3

class EBUR128:
	def __init__(self, filename):
		self.filename = filename
		self.lra_low = None
		self.lra_high = None
		self.th_low_time = 60.0
		self.time_center = 2700.0 # TODO: Also see some instances and calculate average
		self.candidates = []

	def process_lra(self):
		with open(self.filename) as f:
			while f:
				line = f.readline()
				if not line:
					break
				if line[:19] == 'lavfi.r128.LRA.low=':
					self.lra_low = float(line.split('=')[1])
				elif line[:20] == 'lavfi.r128.LRA.high=':
					self.lra_high = float(line.split('=')[1])

	def process_misc(self):
		with open(self.filename) as f:
			louder = False
			while f:
				line = f.readline()
				if not line:
					break
				if line[:6] == 'frame:':
					pts_time = float(line.split(':')[-1])
				elif line[:13] == 'lavfi.r128.S=':
					s = float(line.split('=')[-1])
					if s > self.lra_low:
						louder_last = pts_time
					if not louder and s > self.lra_low:
						louder = True
						start_time = pts_time
					elif louder and pts_time > louder_last + self.th_low_time and s < self.lra_low:
						self.candidates.append((start_time, louder_last))
						louder = False

	def find_the_best(self):
		found_best = False
		for cand in self.candidates:
			if self.time_center < cand[0]:
				score = cand[0] - self.time_center
			elif self.time_center <= cand[1]:
				score = 0.0
			else:
				score = self.time_center - cand[1]
			if not found_best or score < best_score:
				best_score = score
				best = cand
				found_best = True
		if found_best:
			return best

	def process(self):
		self.process_lra()
		self.process_misc()
		best = self.find_the_best()
		print(f'seek_start={best[0]}')
		print(f'seek_end={best[1]}')

if __name__=='__main__':
	import sys
	obj = EBUR128(sys.argv[1])
	obj.process()
