import os

import converters
import utils

input_dir = "input"
work_dir = "work"
width = 1920
height = 1080
framerate = 30
input_extension = ".png"
first_pic_length = 15
other_pic_length = 15
different_length_last_pic = False
last_pic_file_name = "___ZZZZ_IMG_9844_LI.jpg"
last_pic_length = 15
loop = True
transition_length = 0.5
output_file = "output.mp4"

incomplete_pics = os.listdir (input_dir)
if different_length_last_pic:
	if last_pic_file_name not in incomplete_pics:
		raise Exception ("Invalid last pic file name!")
	incomplete_pics.remove (last_pic_file_name)
	incomplete_pics.append (last_pic_file_name)

incomplete_pics.sort (key = lambda incomplete_pic: int (incomplete_pic.replace (input_extension, "")))

pics = [utils.join_path_segments (input_dir, input_file) for input_file in incomplete_pics]

# Fix the rotation of all pics first
for pic_index in range (len (pics)):
	pics [pic_index] = converters.copy_to_work_dir (pics [pic_index])
	pics [pic_index] = converters.fix_rotation (pics [pic_index])

segments = []

for pic_index in range (len (pics)):
	if pic_index == 0:
		pic_length = first_pic_length
	elif pic_index == len (pics) - 1:
		pic_length = last_pic_length
	else:
		pic_length = other_pic_length
	long_video = converters.convert_image_to_video (pics [pic_index], pic_length, width, height, framerate, work_dir = work_dir)
	if pic_index + 1 <= len (pics) - 1:
		short_video = converters.convert_image_to_video (pics [pic_index + 1], transition_length, width, height, framerate, work_dir = work_dir)
	else:
		if loop:
			short_video = converters.convert_image_to_video (pics [0], transition_length, width, height, framerate, work_dir = work_dir)
		else:
			short_video = "!black"
	segments.append (converters.create_transition_video (long_video, short_video, width, height, pic_length, transition_length, framerate, work_dir = work_dir))

converters.concat (output_file, *segments, encoder_options = "-c:v libx264 -preset veryslow -crf 15 -tune stillimage")

converters.copy_from_work_dir (output_file, os.getcwd () + os.sep)

