#! /usr/bin/python3

import sys


class EBUR128:
	def __init__(self, filename):
		self.filename = filename
		self.lra_low = None
		self.lra_high = None
		self.th_low_time = 60.0
		self.th_add_db = -10.0;
		self.time_add_start = -3.0
		self.time_add_end = 3.0
		self.time_range_start = None
		self.time_range_end = None
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
		sys.stderr.write(f'LRA.low = {self.lra_low:.1f} dB\n')

	def process_misc(self):
		th = self.lra_low + self.th_add_db
		with open(self.filename) as f:
			louder = False
			while f:
				line = f.readline()
				if not line:
					break
				if line[:6] == 'frame:':
					pts_time = float(line.split(':')[-1])
				elif line[:13] == 'lavfi.r128.S=':
					if self.time_range_start and pts_time < self.time_range_start:
						continue
					if self.time_range_end and pts_time >= self.time_range_end:
						continue
					s = float(line.split('=')[-1])
					if s > th:
						louder_last = pts_time
					if not louder and s > th:
						louder = True
						start_time = pts_time
					elif louder and pts_time > louder_last + self.th_low_time and s < th:
						self.candidates.append((start_time, louder_last))
						louder = False
						sys.stderr.write(f'candidate: {start_time:.1f} -> {louder_last:.1f} length {louder_last-start_time:.1f}\n')
			if louder:
				self.candidates.append((start_time, louder_last))

			if not self.candidates:
				sys.stderr.write(f'Warning: {self.filename}: No candidates are found. th={th}\n')

	def find_the_best(self):
		found_best = False
		for cand in self.candidates:
			if self.time_candidate_center:
				if self.time_candidate_center < cand[0]:
					score = cand[0] - self.time_candidate_center
				elif self.time_candidate_center <= cand[1]:
					score = 0.0
				else:
					score = self.time_candidate_center - cand[1]
			else:
				score = cand[1] - cand[0]
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
		print(f'seek_start={best[0] + self.time_add_start}')
		print(f'seek_end={best[1] + self.time_add_end}')

if __name__=='__main__':
	import argparse
	import sys
	parser = argparse.ArgumentParser(
			prog=sys.argv[0],
			description='Calculate cut-in and -out point from the loudness data'
	)
	parser.add_argument('ebur128_file')
	parser.add_argument('--time-candidate-center', default=None)
	parser.add_argument('--time-add-start', default=-3.0)
	parser.add_argument('--time-add-end', default=+3.0)
	parser.add_argument('--time-range-start', default=None)
	parser.add_argument('--time-range-end', default=None)
	args = parser.parse_args()

	obj = EBUR128(args.ebur128_file)
	obj.time_candidate_center = float(args.time_candidate_center) if args.time_candidate_center else None
	obj.time_add_start = float(args.time_add_start)
	obj.time_add_end = float(args.time_add_end)
	obj.time_range_start = float(args.time_range_start) if args.time_range_start else None
	obj.time_range_end = float(args.time_range_end) if args.time_range_end else None

	obj.process()
