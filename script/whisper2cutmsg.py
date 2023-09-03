#! /usr/bin/env python3

import argparse
import json
import re
import sys


def _text_filter(t):
	t = t.replace('皆を', '御名を')
	t = t.replace('皆に', '御名に')
	# t = t.replace('上乾いて', '飢え乾いて')
	t = t.replace('耶穌キリスト', 'イエスキリスト')
	t = t.replace('支援', '詩篇')
	t = t.replace('見言葉', '御言葉')
	# t = t.replace('堺シャロム福音教会', '栄シャローム福音教会')
	# t = t.replace('堺', '栄')
	return t


class Detector:
	def get_scores(self, segment):
		'''
		Returns a list or touple of touples containing these items.
		- index offset the score will be added
		- score to add
		The sum of the score should be 0.
		'''
		return None


class DetectorRegex(Detector):
	def __init__(self, regex, scores):
		self.regex = re.compile(regex)
		self.scores = scores

	def get_scores(self, segment):
		if self.regex.match(segment.text):
			return self.scores
		else:
			return None


class DetectorSilence(Detector):
	def __init__(self, th1, th2):
		self.th1, self.th2 = th1, th2

	def get_scores(self, segment):
		if not segment.prev:
			return None
		silence = segment.start - segment.prev.end
		if silence < self.th1:
			return None
		score = min((silence - self.th1) / (self.th2 - self.th1), 1.0)
		return ((-1, -score), (0, +score))

_detectors_eiji_begin = [
	# before the congregation sitting
	DetectorRegex(r'.*改めまして.*おはようございます', ((0, -1), (60, +0.5), (61, +0.5))),
	DetectorRegex(r'.*お近くの方とご挨拶して', ((0, -1), (60, +0.5), (61, +0.5))),
	DetectorRegex(r'.*挨拶していただ', ((0, -1), (60, +0.5), (61, +0.5))),
	DetectorRegex(r'.*お近くの方と', ((0, -1), (60, +0.5), (61, +0.5))),

	# prayer
	DetectorRegex(r'.*一言お祈りいたします', ((0, -1), )),
	DetectorRegex(r'.*耳を傾ける.*恵みを感謝します', ((3, -1), (12, +0.5), (13, +0.5))),
	DetectorRegex(r'.*あなたを(|教師として)歓迎', ((3, -1), (11, +0.5), (12, +0.5))),
	DetectorRegex(r'.*お語りください', ((1, -1), (8, +0.5), (9, +0.5))),
	DetectorRegex(r'.*イエスキリストの御名によって.*お祈りします', ((0, -1), (11, +0.5), (12, +0.5))),
	DetectorRegex(r'.*(祝福して?|心から期待して?)お祈り(|いた)します.*アメン', ((0, -1), (+1, 0.2), (+2, 0.3), (+3, 0.5))),

	# Sunday school and short announcement
	DetectorRegex(r'.*今日も楽しい教会学校があります', ((0, -1), (7, +0.5), (8, +0.5))),
	DetectorRegex(r'.*教会学校のお?友達は', ((0, -1), (20, +0.5), (20, +0.5))),
	DetectorRegex(r'.*私たち今.*からご一緒しております', ((0, -1), (30, +0.5), (31, +0.5))),
	DetectorRegex(r'.*(旧約|新約)聖書.*[1-9][0-9]*ページ', ((0, -0.5), (21, +0.1), (22, +0.2), (23, +0.2))),
	DetectorRegex(r'.*耳を傾けていきたい', ((-40, -0.2), (-39, -0.2), (-38, -0.2), (-37, -0.2), (-36, -0.2), (-2, +0.3), (-1, +0.3), (0, +0.4))),

	DetectorSilence(1.0, 5.0),
	DetectorRegex(r'新聞の投書欄に', ((-1, -1), (0, 1))),
	DetectorRegex(r'(昨日|曜日).*新聞.*に', ((-1, -1), (0, 1))),
	DetectorRegex(r'(昨日|曜日)(は|の)', ((-1, -0.1), (0, 0.1))),

	## These features are not so important but might make the result roboust.
	# words in sermon but not used in the greeting
	DetectorRegex(r'.*(思います|けれども|感じました|わけです|であります|ということです)$', ((0, +0.02), )),
	DetectorRegex(r'(ですから|いずれにせよ)$', ((0, +0.02), )),
	# experiences, etc., words should not used in the greeting
	DetectorRegex(r'.*(シアトル|バイブルカレッジ|ルームメイト|原文|依存症)', ((0, +0.05), )),

	DetectorRegex(r'.*(いるからです|いくべきです|だからです|ことでしょう|んです)$', ((0, 0.09), )), # chie
	DetectorRegex(r'.*皆さんで一緒に', ((0, 0.09), )), # chie
	DetectorRegex(r'(なぜなら|そしてそ(の|れ)|なおさらのこと)', ((0, 0.09), )), # chie
]

_detectors_eiji_end = [
	# about to conclude
	DetectorRegex(r'.*いかがでしょうか', ((1, -0.5), (2, -0.5), (19, +0.6), (20, +0.4))),
	DetectorRegex(r'.*ではないでしょうか', ((0, -0.3), (20, +0.1), (21, +0.1), (22, +0.1))),
	DetectorRegex(r'.*聖霊様来てください', ((0, -0.5), (3, +0.3), (4, +0.2))),
	DetectorRegex(r'(アー?メン *)?祈ります', ((0, -1), (1, +0.8), (2, +0.2))),
	DetectorRegex(r'.*一言お祈りいたします', ((0, -1), (1, +1))), # chie
	DetectorSilence(1.0, 10.0),
	# beginning of prayer
	DetectorRegex(r'.*愛する天のお父様', ((-3, -0.5), (-2, +0.5), (0, +1))),
	DetectorRegex(r'.*あなたの御名を賛美します', ((-4, -0.5), (-3, +0.5), (0, +1))),
	DetectorRegex(r'.*感謝します', ((-5, -0.5), (-4, -0.5), (0, +1))),
	DetectorRegex(r'.*主は.*ご存知であります', ((-15, -0.3), (-2, +0.3))),
	DetectorRegex(r'.*今望んでください', ((-17, -0.3), (-2, +0.3))),
	DetectorRegex(r'.*あなたの御前に', ((-17, -0.3), (0, +0.3))),
	DetectorRegex(r'.*あなたは.*神様で', ((-17, -0.3), (0, +0.3))),

	## These features are not so important but might make the result roboust.
	# words in sermon but not used in prayer
	DetectorRegex(r'.*(んです|んです|思います|いたしました|けれども|感じました|だったわけです)$', ((0, -0.02), )),
	DetectorRegex(r'(ですから|いずれにせよ)$', ((0, -0.02), )),
	DetectorRegex(r'.*(いるからです|いくべきです|だからです|ことでしょう|んです)$', ((0, -0.09), )), # chie
	DetectorRegex(r'.*皆さんで一緒に', ((0, -0.09), )), # chie
	DetectorRegex(r'(なぜなら|そしてそ(の|れ)|なおさらのこと)', ((0, -0.09), )), # chie
	# experiences, etc.
	DetectorRegex(r'.*(シアトル|バイブルカレッジ|ルームメイト|英会話スクール|リビングバイブル)', ((0, -0.02), )),
	DetectorRegex(r'.*(私は|私にとって)', ((0, -0.02), )),
	DetectorRegex(r'.*皆様は', ((0, -0.02), )),
	# prayer
	DetectorRegex(r'.*できますように', ((0, +0.1), )),
	#DetectorRegex(r'.*感謝いたします', ((0, +0.5), )),
	DetectorRegex(r'.*主よ', ((0, +0.05), )),
	DetectorRegex(r'.*ておられます$', ((0, +0.1), )),
	DetectorRegex(r'.*手を置いていただきたいと思います', ((0, +0.1), )),
	DetectorRegex(r'.*(癒されよ|健やかになれ|解決されよ)$', ((0, +0.1), )),
	DetectorRegex(r'.*祝福してお祈りします', ((0, +0.2), )),
	DetectorRegex(r'.*個人的に神様の前に', ((0, +0.1), )),
	DetectorRegex(r'.*祈る時を持ちたい', ((0, +0.3), )),
	DetectorRegex(r'.*アー?メン', ((0, +0.01), )),
	DetectorRegex(r'.*しばらく.*御言葉に応答して', ((0, +0.1), )),
	DetectorRegex(r'.*お祈りする時間を持ちたいと思います', ((0, +0.3), )),
]


class WhisperSegment:
	def __init__(self, segment):
		self.text = _text_filter(segment['text'])
		self.start = segment['start']
		self.end = segment['end']
		self.avg_logprob = segment['avg_logprob']
		self.no_speech_prob = segment['no_speech_prob']
		self.score_sum = 0.0
		self.prev, self.next = None, None


class WhisperData:
	def __init__(self, json_file):
		data = json.load(open(json_file))
		self.segments = []
		for seg in data['segments']:
			self.segments.append(WhisperSegment(seg))
		prev = None
		for seg in self.segments:
			seg.prev = prev
			prev = seg
		for seg in self.segments:
			if seg.prev:
				seg.prev.next = seg

	def reset_score(self):
		for seg in self.segments:
			seg.score_sum = 0.0

	def length_time(self):
		return self.segments[-1].end

	def apply_detectors(self, detectors):
		for d in detectors:
			for ix, seg in enumerate(self.segments):
				scores = d.get_scores(seg)
				if not scores:
					continue
				for o, v in scores:
					ixo = ix + o
					if 0 <= ixo < len(self.segments):
						self.segments[ixo].score_sum += v

	def calculate_cutpoint(self, range_time=None):
		a = 0.0
		cand = 0
		a_min = 0.0
		for ix, seg in enumerate(self.segments):
			a += seg.score_sum
			if range_time:
				if range_time[1] < seg.start or seg.end < range_time[0]:
					continue
			if a < a_min:
				cand = ix + 1
				a_min = a
		return cand


if __name__ == '__main__':
	parser = argparse.ArgumentParser(
			prog=sys.argv[0],
			description='Identify cut-in and -out point of the message from Whisper speech recognition data'
	)
	parser.add_argument('json_file')
	parser.add_argument('-b', '--begin', action='store_true')
	parser.add_argument('-e', '--end', action='store_true')
	parser.add_argument('-v', '--verbose', action='count')
	parser.add_argument('--dialog-log', action='store')
	args = parser.parse_args()

	wd = WhisperData(args.json_file)

	cut_begin, cut_end = -1, -1
	cut_begin_score, cut_end_score = None, None
	if args.begin:
		wd.reset_score()
		wd.apply_detectors(_detectors_eiji_begin)
		cut_begin = wd.calculate_cutpoint((0.0, wd.length_time() - 600.0))

		cut_begin_score = [seg.score_sum for seg in wd.segments]

	if args.end:
		wd.reset_score()
		wd.apply_detectors(_detectors_eiji_end)
		cut_end = wd.calculate_cutpoint((600.0, wd.length_time()))

		cut_end_score = [seg.score_sum for seg in wd.segments]

	ff_filters = []
	cut_begin_t = 0.0
	if cut_begin > 0:
		seg = wd.segments[cut_begin]
		silence = seg.start - seg.prev.end
		cut_begin_t = seg.start # - min(3.0, silence) # TODO: Why Whisper says start time earlier than actual?

	cut_end_t = wd.segments[-1].end
	if cut_end > 0:
		seg = wd.segments[cut_end]
		silence = seg.start - seg.prev.end
		cut_end_t = seg.prev.end + min(4.0, silence)

	print(f'seek_start={cut_begin_t:0.1f}')
	print(f'seek_end={cut_end_t:0.1f}')

	if args.dialog_log:
		with open(args.dialog_log, 'w') as f:
			for ix, seg in enumerate(wd.segments):
				if ix == cut_begin:
					f.write('cut-begin\n')
				if ix == cut_end:
					f.write('cut-end\n')
				silence = seg.start - seg.prev.end if seg.prev else 0.0
				score_texts = ''
				if cut_begin_score:
					score_texts += f'\t{cut_begin_score[ix]:.2f}'
				if cut_end_score:
					score_texts += f'\t{cut_end_score[ix]:.2f}'
				f.write(f'{silence:.1f} [{seg.start:.1f} {seg.end:.1f}]{score_texts}\t{seg.text}\n')
