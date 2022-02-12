

# this class is just a wrapper class around the open function that can be used by with keyword 
class File(object):
	def __init__(self, file_name, method):
		self.file_obj = open(file_name, method)

	# this returns the object that file_obj points to, created by the open function
	def __enter__(self):
		return self.file_obj

	# this invokes the inherent method from the object to close access
	def __exit__(self, type, value, traceback):
		self.file_obj.close()


# with File('testfile/original.txt', "w") as opened_file:
#     opened_file.write("Hola! te amo")


