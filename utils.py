import os
import subprocess

bad_chars = " '\"()&$"

def escape_string (string):
	for bad_char in bad_chars:
		string = string.replace (bad_char, "\\" + bad_char)
	return string

def remove_extension (file_name):
	return '.'.join (file_name.split ('.') [:-1])

def get_extension (file_name):
	return file_name.split ('.') [-1]

def join_path_segments (*segments):
	return os.sep.join (segments)

def file_to_path (file, work_dir = "work"):
	return join_path_segments (work_dir, escape_string (file))

def path_exists (path):
	return subprocess.run (f"[ -f {path} ] && return 0 ; return 1", shell = True).returncode == 0

def get_input_and_output_paths_with_output_file (input_file, work_dir, output_file_suffix, extension = None):
	output_file = remove_extension (input_file) + output_file_suffix + "." + (get_extension (input_file) if extension is None else extension)
	print (output_file)
	return file_to_path (input_file, work_dir), output_file, file_to_path (output_file, work_dir)
