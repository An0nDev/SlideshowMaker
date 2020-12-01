import os

import utils
import converters

pics_dir = "pics"
vids_dir = "vids"
width = 1440
height = 1080
framerate = 30
first_item_length = 10
item_length = 3
last_item_length = 10
transition_time = 0.5
output_name = "out.mp4"

pics = os.listdir (pics_dir)
pics.sort (key = str.lower)

sequence = []

for pic in pics:
	removed_extension_pic = utils.remove_extension (pic)
	pic_with_path = utils.join_path_segments (pics_dir, pic)
	rotation_fixed_file_name = utils.join_path_segments (pics_dir, removed_extension_pic + "_rotation_fixed.png")
	long_file_name = utils.join_path_segments (vids_dir, removed_extension_pic + "_long.mp4")
	short_file_name = utils.join_path_segments (vids_dir, removed_extension_pic + "_short.mp4")
	merged_file_name = utils.join_path_segments (vids_dir, removed_extension_pic + "_merged.mp4")
	sequence.append ([pic_with_path, rotation_fixed_file_name, long_file_name, short_file_name, merged_file_name])

print (len (sequence))
print (sequence)

# os._exit (0)

for item_index in range (len (sequence)):
	item = sequence [item_index]
	print (item)
	rotation_fixed_input_and_output = (item [0], item [1])
	long_input_and_output = (item [1], item [2])
	short_input_and_output = (item [1], item [3])
	if item_index == 0:
		long_and_merged_length = first_item_length
	elif item_index == len (sequence) - 1:
		long_and_merged_length = last_item_length
	else:
		long_and_merged_length = item_length
	if not os.path.exists (item [1]):
		converters.fix_rotation (item [0], item [1])
	if not os.path.exists (item [2]):
		converters.convert_image_to_video (item [1], long_and_merged_length, width, height, framerate, item [2])
	if not os.path.exists (item [3]):
		converters.convert_image_to_video (item [1], transition_time, width, height, framerate, item [3])
	if item_index + 1 >= len (sequence):
		next_item_short_path = "!black"
	else:
		next_item = sequence [item_index + 1]
		if not os.path.exists (next_item [1]):
			converters.fix_rotation (next_item [0], next_item [1])
		if not os.path.exists (next_item [3]):
			converters.convert_image_to_video (next_item [1], transition_time, width, height, framerate, next_item [3])
		next_item_short_path = next_item [3]
	if not os.path.exists (item [4]):
		converters.create_transition_video (item [3], next_item_short_path, width, height, long_and_merged_length, transition_time, item [4])

print (item [4] for item in sequence)

converters.concat (output_name, *(item [4] for item in sequence))
