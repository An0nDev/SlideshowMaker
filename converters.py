import subprocess
import shutil
import os

import utils

def copy_to_work_dir (unescaped_input_path, work_dir = "work"):
	input_file = unescaped_input_path.split (os.sep) [-1]
	output_path = utils.file_to_path (input_file, work_dir)
	if utils.path_exists (output_path):
		return input_file
	command = f"cp {utils.escape_string (unescaped_input_path)} {output_path}"
	subprocess.run (command, shell = True, check = True)
	return input_file

def copy_from_work_dir (input_file, unescaped_output_path, work_dir = "work"):
	input_path = utils.file_to_path (input_file, work_dir = work_dir)
	output_path = utils.escape_string (unescaped_output_path)
	command = f"cp {input_path} {output_path}"
	subprocess.run (command, shell = True, check = True)
	return output_path

def fix_rotation (input_file, work_dir = "work", output_file_suffix = "_rotated"):
	input_path, output_file, output_path = utils.get_input_and_output_paths_with_output_file (input_file, work_dir, output_file_suffix)
	if utils.path_exists (output_path):
		return output_file
	def copy_to_output (): subprocess.run (f"cp {input_path} {output_path}", shell = True, check = True)
	exiftool_command = f"exiftool -Orientation {input_path}"
	exiftool_output = subprocess.run (exiftool_command, shell = True, check = True, capture_output = True).stdout.decode ("utf-8")
	if exiftool_output == "":
		copy_to_output ()
		return output_file
	# print (exiftool_output)
	# exiftool_output should now be "Orientation                     : Rotate 90 CW\n"
	exiftool_output = exiftool_output.replace ("\n", "")
	exiftool_output = exiftool_output.split (':') [1].strip ()
	if exiftool_output == "Horizontal (normal)" or exiftool_output == "Unknown (0)":
		copy_to_output ()
		return output_file
	exiftool_output = exiftool_output.replace ("Rotate ", "")
	# exiftool_output is now "90 CW"
	rotation, direction = exiftool_output.split (' ')
	rotation = int (rotation)
	# rotation, direction are now 90, "CW"
	if direction == "CCW":
		rotation = 360 - rotation
	else:
		assert direction == "CW", f"Invalid direction {direction} (not CCW or CW)"
	rotation = rotation % 360
	assert rotation in [0, 90, 180, 270], "Non-multiples of 90 degrees not supported"
	rotation_in_radians = f"{rotation / 180}*PI"
	# print (rotation_in_radians)
	flip_width_and_height = rotation % 180 == 90
	# print (flip_width_and_height)
	rotation_filter = f"rotate=angle={rotation_in_radians}:bilinear=0"
	if flip_width_and_height: rotation_filter += ":ow=ih:oh=iw"
	command = f"ffmpeg -i {input_path} -filter:v {rotation_filter} {output_path}"
	# print (command)
	subprocess.run (command, shell = True, check = True)
	return output_file

def convert_image_to_video (input_file, length, width, height, framerate, work_dir = "work", output_file_suffix = None):
	if output_file_suffix == None: output_file_suffix = f"_{length}s" # can't access length argument in arguments so I had to use None as a placeholder and then check in the function body :/
	input_path, output_file, output_path = utils.get_input_and_output_paths_with_output_file (input_file, work_dir, output_file_suffix, extension = "mp4")
	if utils.path_exists (output_path):
		return output_file
	subprocess.run (f"cat {input_path} | ffmpeg -f image2pipe -i - -filter:v scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:\\(ow-iw\\)/2:\\(oh-ih\\)/2 -f image2 - | ffmpeg -framerate 1/{length} -f image2pipe -i - -c:v libx264 -r {framerate} -t {length} -pix_fmt yuv420p {output_path}", shell = True, check = True)
	return output_file

def create_transition_video (input_file_1, input_file_2, width, height, time_per_picture, transition_time, framerate, work_dir = "work", output_file_suffix = "_merged"):
	input_path_1, output_file, output_path = utils.get_input_and_output_paths_with_output_file (input_file_1, work_dir, output_file_suffix, extension = "mp4")
	if utils.path_exists (output_path):
		return output_file
	input_1_segment = f"-i {input_path_1}"
	black_input_string = f"-f lavfi -i color=black:r={framerate}:s={width}x{height}"
	if input_file_2 == "!black":
		input_2_segment = black_input_string
		input_2_mods = f"trim=duration={transition_time},"
	else:
		input_path_2 = utils.file_to_path (input_file_2, work_dir)
		input_2_segment = f"-i {input_path_2}"
		input_2_mods = ""
	command = f"ffmpeg {input_1_segment} {input_2_segment} {black_input_string} -filter_complex \
\"[0:v]format=pix_fmts=yuva420p,fade=t=out:st={time_per_picture - transition_time}:d={transition_time}:alpha=1,setpts=PTS-STARTPTS[va0];\
[1:v]format=pix_fmts=yuva420p,{input_2_mods}fade=t=in:st=0:d={transition_time}:alpha=1,setpts=PTS-STARTPTS+{time_per_picture - transition_time}/TB[va1];\
[2:v]trim=duration={time_per_picture}[over];\
[over][va0]overlay[over1];\
[over1][va1]overlay=format=yuv420[outv]\" \
-vcodec libx264 -map [outv] {output_path}"
	subprocess.run (command, shell = True, check = True)
	return output_file
	# print (command)

def concat (output_file, *input_files, encoder_options = None, work_dir = "work"):
	input_paths = [utils.file_to_path (input_file, work_dir) for input_file in input_files]
	output_path = utils.file_to_path (output_file, work_dir)
	if utils.path_exists (output_path):
		return output_file
	inputs_segment = " ".join (f"-i {input_path}" for input_path in input_paths)
	filter_inputs_segment = " ".join (f"[{input_index}:v]" for input_index in range (len (input_paths)))
	if encoder_options is None:
		encoder_options = ""
	else:
		encoder_options = " " + encoder_options + " "
	command = f"ffmpeg {inputs_segment} -filter_complex \"{filter_inputs_segment} concat=n={len (input_paths)}:v=1 [v]\" -map [v]{encoder_options}{output_path}"
	subprocess.run (command, shell = True, check = True)
	return output_file
	# print (command)

