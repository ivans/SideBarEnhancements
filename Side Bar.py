# coding=utf8
import sublime, sublime_plugin
import os, sys
import functools
import re

#NOTES
# A "directory" for this plugin is a "directory"
# A "directory" for a user is a "folder"

class SideBarSelection:

	def __init__(self, paths):
		
		self._paths = paths

		self._obtained_selection_information_basic = False
		self._obtained_selection_information_extended = False

	def hasDirectories(self):
		self._obtainSelectionInformationBasic()
		return self._has_directories

	def hasFiles(self):
		self._obtainSelectionInformationBasic()
		return self._has_files

	def hasOnlyDirectories(self):
		self._obtainSelectionInformationBasic()
		return self._only_directories

	def hasOnlyFiles(self):
		self._obtainSelectionInformationBasic()
		return self._only_files
	
	def hasImages(self):
		return self.hasFilesWithExtension('gif|jpg|jpeg|png')

	def hasFilesWithExtension(self, extensions):
		extensions = re.compile(extensions+'$', re.I);
		for item in self.getSelectedFiles():
			if extensions.search(item.path()):
				return True;
		return False

	def getSelectedItems(self):
		self._obtainSelectionInformationExtended()
		return self._files + self._directories;

	def getSelectedDirectories(self):
		self._obtainSelectionInformationExtended()
		return self._directories;

	def getSelectedFiles(self):
		self._obtainSelectionInformationExtended()
		return self._files;

	def getSelectedDirectoriesOrDirnames(self):
		self._obtainSelectionInformationExtended()
		return self._directories_or_dirnames;

	def getSelectedImages(self):
		return self.getSelectedFilesWithExtension('gif|jpg|jpeg|png')
		
	def getSelectedFilesWithExtension(self, extensions):
		items = []
		extensions = re.compile(extensions+'$', re.I);
		for item in self.getSelectedFiles():
			if extensions.search(item.path()):
				items.append(item)
		return items
		
	def _obtainSelectionInformationBasic(self):
		if not self._obtained_selection_information_basic:
			self._obtained_selection_information_basic = True

			self._has_directories = False
			self._has_files = False
			self._only_directories = False
			self._only_files = False

			for path in self._paths:
				if self._has_directories == False and os.path.isdir(path):
					self._has_directories = True
				if self._has_files == False and os.path.isdir(path) == False:
					self._has_files = True
				if self._has_files and self._has_directories:
					break

			if self._has_files and self._has_directories:
				self._only_directories = False
				self._only_files 	= False
			elif self._has_files:
				self._only_files 	= True
			elif self._has_directories:
				self._only_directories = True
	
	def _obtainSelectionInformationExtended(self):
		if not self._obtained_selection_information_extended:
			self._obtained_selection_information_extended = True

			self._directories = []
			self._files = []
			#selected directories and/or the dirname of selected files if any
			self._directories_or_dirnames = []

			for path in self._paths:
				if os.path.isdir(path):
					item = SideBarItem(path, True)
					if item not in self._directories:
						self._directories.append(item)
					if item not in self._directories_or_dirnames:
						self._directories_or_dirnames.append(item)
				else:
					item = SideBarItem(path, False)
					if item not in self._files:
						self._files.append(item)
					item = SideBarItem(os.path.dirname(path), True)
					if item not in self._directories_or_dirnames:
						self._directories_or_dirnames.append(item)

class SideBarItem:

	def __init__(self, path, is_directory):
		self._path = path
		self._is_directory = is_directory

	def path(self):
		return self._path

	def pathSystem(self):
		return self.path().encode(sys.getfilesystemencoding())

	def pathWithoutProject(self):
		path = self.path()
		for directory in sublime.active_window().folders():
			path = re.sub('^'+re.escape(directory), '', path)
		return path.replace('\\', '/')
				
	def pathRelativeFromProject(self):
		return re.sub('^/', '', self.pathWithoutProject())

	def pathRelativeFromProjectEncoded(self):
		import urllib
		return urllib.quote(self.pathRelativeFromProject().encode('utf-8'))

	def pathAbsoluteFromProject(self):
		return self.pathWithoutProject()

	def pathAbsoluteFromProjectEncoded(self):
		import urllib
		return urllib.quote(self.pathAbsoluteFromProject().encode('utf-8'))

	def uri(self):
		import urllib
		return 'file:'+urllib.pathname2url(self.path().encode('utf-8'));

	def join(self, name):
		return os.path.join(self.path(), name)

	def dirname(self):
		branch, leaf = os.path.split(self.path())
		return branch;

	def dirnameSystem(self):
		return self.dirname().encode(sys.getfilesystemencoding())

	def dirnameCreate(self):
		try:
			os.makedirs(self.dirname())
		except:
			pass

	def name(self):
		branch, leaf = os.path.split(self.path())
		return leaf;

	def nameSystem(self):
		return self.name().encode(sys.getfilesystemencoding())

	def nameEncoded(self):
		import urllib
		return urllib.quote(self.name().encode('utf-8'));
	
	def namePretty(self):
		return self.name().replace(self.extension(), '').replace('-', ' ').replace('_', ' ');

	def open(self):
		import subprocess 
		subprocess.Popen([self.nameSystem()], cwd=self.dirnameSystem(), shell=True)
	
	def edit(self):
		sublime.active_window().open_file(self.path())

	def isDirectory(self):
		return self._is_directory
	
	def isFile(self):
		return self.isDirectory() == False

	def contentUTF8(self):
		data = file(self.path(), "r").read();
		try:
			return unicode(data, "utf-8")
		except:
			return data

	def contentBinary(self):
		return file(self.path(), "rb").read()

	def contentBase64(self):
		return 'data:'+self.mime()+';base64,'+(file(self.path(), "rb").read().encode("base64").replace('\n', ''))

	def reveal(self):
		sublime.active_window().run_command("open_dir", {"dir": self.dirname(), "file": self.name()} )

	def write(self, content):
		file(self.path(), 'w+').write(content)

	def mime(self):
		import mimetypes
		return mimetypes.guess_type(self.path())[0] or 'application/octet-stream'

	def extension(self):
		return os.path.splitext('name'+self.name())[1].lower()

	def exists(self):
		return os.path.isdir(self.path()) or os.path.isfile(self.path())
	
	def create(self):
		if self.isDirectory():
			self.dirnameCreate()
			os.makedirs(self.path())
		else:
			self.dirnameCreate()
			self.write('')

	def move(self, location):
		location = SideBarItem(location, os.path.isdir(location));
		if location.exists():
			return False
		else:
			location.dirnameCreate();
			os.rename(self.path(), location.path())
			return True

	def copy(self, location):
		location = SideBarItem(location, os.path.isdir(location));
		if location.exists():
			return False
		else:
			location.dirnameCreate();
			import shutil
			if self.isDirectory():
				shutil.copytree(self.path(), location.path())
			else:
				shutil.copy(self.path(), location.path())
			return True

class SideBarFilesNewFileCommand(sublime_plugin.WindowCommand):
	def run(self, paths, name = ""):
		self.window.run_command('hide_panel');
		self.window.show_input_panel("File Name:", name, functools.partial(self.on_done, paths), None, None)

	def on_done(self, paths, name):
		for item in SideBarSelection(paths).getSelectedDirectoriesOrDirnames():
			item = SideBarItem(item.join(name), False)
			if item.exists():
				sublime.error_message("Unable to create file, file or folder exists.")
				self.run(paths, name)
				break
			else:
				try:
					item.create()
					item.edit()
				except:
					sublime.error_message("Unable to create file:\n\n"+item.path())
					self.run(paths, name)
					break
		self.window.run_command('refresh_folder_list');

	def is_enabled(self, paths):
		return len(paths) > 0

class SideBarFilesNewDirectoryCommand(sublime_plugin.WindowCommand):
	def run(self, paths, name = ""):
		self.window.run_command('hide_panel');
		self.window.show_input_panel("Folder Name:", name, functools.partial(self.on_done, paths), None, None)

	def on_done(self, paths, name):
		for item in SideBarSelection(paths).getSelectedDirectoriesOrDirnames():
			item = SideBarItem(item.join(name), True)
			if item.exists():
				sublime.error_message("Unable to create folder, folder or file exists.")
				self.run(paths, name)
				break
			else:
				item.create()
				if not item.exists():
					sublime.error_message("Unable to create folder:\n\n"+item.path())
					self.run(paths, name)
					break
		self.window.run_command('refresh_folder_list');

	def is_enabled(self, paths):
		return len(paths) > 0

class SideBarFilesEditCommand(sublime_plugin.WindowCommand):
	def run(self, paths):
		for item in SideBarSelection(paths).getSelectedFiles():
			item.edit()

	def is_enabled(self, paths):
		return SideBarSelection(paths).hasFiles()

class SideBarFilesOpenCommand(sublime_plugin.WindowCommand):
	def run(self, paths):
		for item in SideBarSelection(paths).getSelectedFiles():
			item.open()

	def is_enabled(self, paths):
		return SideBarSelection(paths).hasFiles()

class SideBarFilesOpenWithEditApplicationsCommand(sublime_plugin.WindowCommand):
	def run(self, paths):
		item = SideBarItem(os.path.join(sublime.packages_path(), 'User', 'SideBarEnhancements', 'Open With', 'Side Bar.sublime-menu'), False)
		if not item.exists():
			item.create()
			item.write("""[
	{"id": "side-bar-files-open-with",
		"children":
		[

			//application 1
			{ 
				"caption": "Photoshop CS4",
				"id": "side-bar-files-open-with-photoshop",     
				  
				"command": "side_bar_files_open_with",     
				"args": {
									"paths": [],
									"application": "C:\\\\Archivos de programa\\\\Adobe\\\\Adobe Photoshop CS4\\\\Photoshop.exe",
									"extensions":"psd|png|jpg|jpeg"  //any file with these extensions
								} 
			},

			//separator
			{"caption":"-"},

			//application 2
			{ 
				"caption": "SeaMonkey",
				"id": "side-bar-files-open-with-seamonkey",  
				     
				"command": "side_bar_files_open_with",     
				"args": {
									"paths": [],
									"application": "C:\\\\Archivos de programa\\\\SeaMonkey\\\\seamonkey.exe",
									"extensions":"" //open all even folders
								} 
			},
			//application n
			{ 
				"caption": "Chrome",
				"id": "side-bar-files-open-with-chrome",    
				   
				"command": "side_bar_files_open_with",     
				"args": {
									"paths": [],
									"application": "C:\\\\Documents and Settings\\\\tito\\\\Configuración local\\\\Datos de programa\\\\Google\\\\Chrome\\\\Application\\\\chrome.exe",
									"extensions":".*" //any file with extension
								} 
			},

			{"caption":"-"}
		]
	}
]""");
		item.edit()

	def is_enabled(self, paths):
		return True

class SideBarFilesOpenWithCommand(sublime_plugin.WindowCommand):
	def run(self, paths, application, extensions):

		application_dir, application_name = os.path.split(application)
		application_dir =  application_dir.encode(sys.getfilesystemencoding())
		application_name = application_name.encode(sys.getfilesystemencoding())

		if extensions == '*':
			extensions = '.*'
		if extensions == '':
			items = SideBarSelection(paths).getSelectedItems()
		else:
			items = SideBarSelection(paths).getSelectedFilesWithExtension(extensions)

		import subprocess 
		for item in items:
			subprocess.Popen([application_name, item.pathSystem()], cwd=application_dir, shell=True)
			
	def is_enabled(self, paths, application, extensions):
		if extensions == '*':
			extensions = '.*'
		if extensions == '':
			return len(paths) > 0
		else :
			return SideBarSelection(paths).hasFilesWithExtension(extensions)

class SideBarFilesFindInSelectedCommand(sublime_plugin.WindowCommand):
	def run(self, paths):
		self.window.run_command('hide_panel');
		self.window.run_command("show_panel", {"panel": "find_in_files", "location": ",".join(paths)})

	def is_enabled(self, paths):
		return len(paths) > 0
			
class SideBarFilesFindInParentCommand(sublime_plugin.WindowCommand):
	def run(self, paths):
		items = []
		for item in SideBarSelection(paths).getSelectedItems():
			items.append(item.dirname())
		self.window.run_command('hide_panel');
		self.window.run_command("show_panel", {"panel": "find_in_files", "location": ",".join(items)})

	def is_enabled(self, paths):
		return len(paths) > 0

class SideBarFilesFindInProjectCommand(sublime_plugin.WindowCommand):
	def run(self):
		self.window.run_command('hide_panel');
		self.window.run_command('show_panel', {"panel": "find_in_files", "location": "<open folders>"});

class SideBarFilesCutCommand(sublime_plugin.WindowCommand):
	def run(self, paths):
		s = sublime.load_settings("SideBar Files.sublime-settings")
		s.set('cut', paths)
		s.set('copy', [])
		if len(paths) > 1 :
			sublime.status_message("Items cut")
		else :
			sublime.status_message("Item cut")

	def is_enabled(self, paths):
		return len(paths) > 0

class SideBarFilesCopyCommand(sublime_plugin.WindowCommand):
	def run(self, paths):
		s = sublime.load_settings("SideBar Files.sublime-settings")
		s.set('cut', [])
		s.set('copy', paths)
		if len(paths) > 1 :
			sublime.status_message("Items copied")
		else :
			sublime.status_message("Item copied")

	def is_enabled(self, paths):
		return len(paths) > 0

class SideBarFilesPasteCommand(sublime_plugin.WindowCommand):
	def run(self, paths):
		import shutil
		s = sublime.load_settings("SideBar Files.sublime-settings")
		
		cut = s.get('cut', [])
		copy = s.get('copy', [])

		location = paths[0]
		if os.path.isdir(location) == False:
			location = SideBarItem(os.path.dirname(location), True)
		else:
			location = SideBarItem(location, True)

		for path in cut:
			path = SideBarItem(path, os.path.isdir(path))
			new  = os.path.join(location.path(), path.name())
			try:
				if not path.move(new):
					sublime.error_message("Unable to cut and paste, destination exists.")
					return
			except:
				sublime.error_message("Unable to move:\n\n"+path.path()+"\n\nto\n\n"+new)
				return

		for path in copy:
			path = SideBarItem(path, os.path.isdir(path))
			new  = os.path.join(location.path(), path.name())
			try:
				if not path.copy(new):
					sublime.error_message("Unable to copy and paste, destination exists.")
					return
			except:
				sublime.error_message("Unable to copy:\n\n"+path.path()+"\n\nto\n\n"+new)
				return

		cut = s.set('cut', [])
		self.window.run_command('refresh_folder_list');

	def is_enabled(self, paths):
		s = sublime.load_settings("SideBar Files.sublime-settings")
		return (len(s.get('cut', [])) + len(s.get('copy', []))) > 0

class SideBarFilesCopyNameCommand(sublime_plugin.WindowCommand):
	def run(self, paths):
		to_copy = []
		for item in SideBarSelection(paths).getSelectedItems():
			to_copy.append(item.name())
		
		sublime.set_clipboard("\n".join(to_copy));
		if len(to_copy) > 1 :
			sublime.status_message("Items copied")
		else :
			sublime.status_message("Item copied")

	def is_enabled(self, paths):
		return len(paths) > 0

class SideBarFilesCopyNameEncodedCommand(sublime_plugin.WindowCommand):
	def run(self, paths):
		to_copy = []
		for item in SideBarSelection(paths).getSelectedItems():
			to_copy.append(item.nameEncoded())
		
		sublime.set_clipboard("\n".join(to_copy));
		if len(to_copy) > 1 :
			sublime.status_message("Items copied")
		else :
			sublime.status_message("Item copied")

	def is_enabled(self, paths):
		return len(paths) > 0

class SideBarFilesCopyPathCommand(sublime_plugin.WindowCommand):
	def run(self, paths):
		to_copy = []
		for item in SideBarSelection(paths).getSelectedItems():
			to_copy.append(item.path())
		
		sublime.set_clipboard("\n".join(to_copy));
		if len(to_copy) > 1 :
			sublime.status_message("Items copied")
		else :
			sublime.status_message("Item copied")

	def is_enabled(self, paths):
		return len(paths) > 0

class SideBarFilesCopyPathEncodedCommand(sublime_plugin.WindowCommand):
	def run(self, paths):
		to_copy = []
		for item in SideBarSelection(paths).getSelectedItems():
			to_copy.append(item.uri())
		
		sublime.set_clipboard("\n".join(to_copy));
		if len(to_copy) > 1 :
			sublime.status_message("Items copied")
		else :
			sublime.status_message("Item copied")

	def is_enabled(self, paths):
		return len(paths) > 0

class SideBarFilesCopyPathRelativeCommand(sublime_plugin.WindowCommand):
	def run(self, paths):
		to_copy = []
		for item in SideBarSelection(paths).getSelectedItems():
			to_copy.append(item.pathRelativeFromProject())
		
		sublime.set_clipboard("\n".join(to_copy));
		if len(to_copy) > 1 :
			sublime.status_message("Items copied")
		else :
			sublime.status_message("Item copied")

	def is_enabled(self, paths):
		return len(paths) > 0

class SideBarFilesCopyPathRelativeEncodedCommand(sublime_plugin.WindowCommand):
	def run(self, paths):
		to_copy = []
		for item in SideBarSelection(paths).getSelectedItems():
			to_copy.append(item.pathRelativeFromProjectEncoded())
		
		sublime.set_clipboard("\n".join(to_copy));
		if len(to_copy) > 1 :
			sublime.status_message("Items copied")
		else :
			sublime.status_message("Item copied")

	def is_enabled(self, paths):
		return len(paths) > 0

class SideBarFilesCopyPathAbsoluteCommand(sublime_plugin.WindowCommand):
	def run(self, paths):
		to_copy = []
		for item in SideBarSelection(paths).getSelectedItems():
			to_copy.append(item.pathAbsoluteFromProject())
		
		sublime.set_clipboard("\n".join(to_copy));
		if len(to_copy) > 1 :
			sublime.status_message("Items copied")
		else :
			sublime.status_message("Item copied")

	def is_enabled(self, paths):
		return len(paths) > 0

class SideBarFilesCopyPathAbsoluteEncodedCommand(sublime_plugin.WindowCommand):
	def run(self, paths):
		to_copy = []
		for item in SideBarSelection(paths).getSelectedItems():
			to_copy.append(item.pathAbsoluteFromProjectEncoded())
		
		sublime.set_clipboard("\n".join(to_copy));
		if len(to_copy) > 1 :
			sublime.status_message("Items copied")
		else :
			sublime.status_message("Item copied")

	def is_enabled(self, paths):
		return len(paths) > 0

class SideBarFilesCopyTagAhrefCommand(sublime_plugin.WindowCommand):
	def run(self, paths):
		to_copy = []
		for item in SideBarSelection(paths).getSelectedItems():
			to_copy.append('<a href="'+item.pathAbsoluteFromProjectEncoded()+'">'+item.namePretty()+'</a>')
		
		sublime.set_clipboard("\n".join(to_copy));
		if len(to_copy) > 1 :
			sublime.status_message("Items copied")
		else :
			sublime.status_message("Item copied")

	def is_enabled(self, paths):
		return len(paths) > 0

class SideBarFilesCopyTagImgCommand(sublime_plugin.WindowCommand):

	def run(self, paths):
		to_copy = []
		for item in SideBarSelection(paths).getSelectedImages():
			try:
				image_type, width, height = self.getImageInfo(item.contentBinary())
				to_copy.append('<img src="'+item.pathAbsoluteFromProjectEncoded()+'" width="'+str(width)+'" height="'+str(height)+'" border="0"/>')
			except:
				to_copy.append('<img src="'+item.pathAbsoluteFromProjectEncoded()+'" border="0"/>')

		sublime.set_clipboard("\n".join(to_copy));
		if len(to_copy) > 1 :
			sublime.status_message("Items copied")
		else :
			sublime.status_message("Item copied")

	#Project:http://code.google.com/p/bfg-pages/
	#License:http://www.opensource.org/licenses/bsd-license.php
	def getImageInfo(self, data):
		import StringIO
		import struct
		data = str(data)
		size = len(data)
		height = -1
		width = -1
		content_type = ''

		# handle GIFs
		if (size >= 10) and data[:6] in ('GIF87a', 'GIF89a'):
			# Check to see if content_type is correct
			content_type = 'image/gif'
			w, h = struct.unpack("<HH", data[6:10])
			width = int(w)
			height = int(h)

		# See PNG 2. Edition spec (http://www.w3.org/TR/PNG/)
		# Bytes 0-7 are below, 4-byte chunk length, then 'IHDR'
		# and finally the 4-byte width, height
		elif ((size >= 24) and data.startswith('\211PNG\r\n\032\n')
					and (data[12:16] == 'IHDR')):
			content_type = 'image/png'
			w, h = struct.unpack(">LL", data[16:24])
			width = int(w)
			height = int(h)

		# Maybe this is for an older PNG version.
		elif (size >= 16) and data.startswith('\211PNG\r\n\032\n'):
			# Check to see if we have the right content type
			content_type = 'image/png'
			w, h = struct.unpack(">LL", data[8:16])
			width = int(w)
			height = int(h)

		# handle JPEGs
		elif (size >= 2) and data.startswith('\377\330'):
			content_type = 'image/jpeg'
			jpeg = StringIO.StringIO(data)
			jpeg.read(2)
			b = jpeg.read(1)
			try:
				while (b and ord(b) != 0xDA):
					while (ord(b) != 0xFF): b = jpeg.read(1)
					while (ord(b) == 0xFF): b = jpeg.read(1)
					if (ord(b) >= 0xC0 and ord(b) <= 0xC3):
						jpeg.read(3)
						h, w = struct.unpack(">HH", jpeg.read(4))
						break
					else:
						jpeg.read(int(struct.unpack(">H", jpeg.read(2))[0])-2)
					b = jpeg.read(1)
				width = int(w)
				height = int(h)
			except struct.error:
				pass
			except ValueError:
				pass
		return content_type, width, height

	def is_enabled(self, paths):
		return SideBarSelection(paths).hasImages()

	

class SideBarFilesCopyTagStyleCommand(sublime_plugin.WindowCommand):
	def run(self, paths):
		to_copy = []
		for item in SideBarSelection(paths).getSelectedFilesWithExtension('css'):
			to_copy.append('<link rel="stylesheet" type="text/css" href="'+item.pathAbsoluteFromProjectEncoded()+'"/>')
		
		sublime.set_clipboard("\n".join(to_copy));
		if len(to_copy) > 1 :
			sublime.status_message("Items copied")
		else :
			sublime.status_message("Item copied")

	def is_enabled(self, paths):
		return SideBarSelection(paths).hasFilesWithExtension('css')

class SideBarFilesCopyTagScriptCommand(sublime_plugin.WindowCommand):
	def run(self, paths):
		to_copy = []
		for item in SideBarSelection(paths).getSelectedFilesWithExtension('js'):
			to_copy.append('<script type="text/javascript" src="'+item.pathAbsoluteFromProjectEncoded()+'"></script>')
		
		sublime.set_clipboard("\n".join(to_copy));
		if len(to_copy) > 1 :
			sublime.status_message("Items copied")
		else :
			sublime.status_message("Item copied")

	def is_enabled(self, paths):
		return SideBarSelection(paths).hasFilesWithExtension('js')

class SideBarFilesCopyProjectDirectoriesCommand(sublime_plugin.WindowCommand):
	def run(self, paths):
		to_copy = []
		for directory in sublime.active_window().folders():
			to_copy.append(directory)

		sublime.set_clipboard("\n".join(to_copy));
		if len(to_copy) > 1 :
			sublime.status_message("Items copied")
		else :
			sublime.status_message("Item copied")

	def is_enabled(self, paths):
		return True

class SideBarFilesCopyContentUtf8Command(sublime_plugin.WindowCommand):
	def run(self, paths):
		to_copy = []
		for item in SideBarSelection(paths).getSelectedFiles():
			to_copy.append(item.contentUTF8())

		sublime.set_clipboard("\n".join(to_copy));
		if len(paths) > 1 :
			sublime.status_message("Items content copied")
		else :
			sublime.status_message("Item content copied")

	def is_enabled(self, paths):
		return SideBarSelection(paths).hasFiles()

class SideBarFilesCopyContentBase64Command(sublime_plugin.WindowCommand):
	def run(self, paths):
		to_copy = []
		for item in SideBarSelection(paths).getSelectedFiles():
			to_copy.append(item.contentBase64())

		sublime.set_clipboard("\n".join(to_copy));
		if len(paths) > 1 :
			sublime.status_message("Items content copied")
		else :
			sublime.status_message("Item content copied")

	def is_enabled(self, paths):
		return SideBarSelection(paths).hasFiles()

class SideBarFilesDuplicateCommand(sublime_plugin.WindowCommand):
	def run(self, paths, new = False):
		self.window.run_command('hide_panel');
		self.window.show_input_panel("Duplicate As:", new or paths[0], functools.partial(self.on_done, paths[0]), None, None)

	def on_done(self, old, new):
		item = SideBarItem(old, os.path.isdir(old))
		try:
			if not item.copy(new):
				sublime.error_message("Unable to duplicate, destination exists.")
				self.run([old], new)
		except:
			sublime.error_message("Unable to move:\n\n"+old+"\n\nto\n\n"+new)
			self.run([old], new)
		self.window.run_command('refresh_folder_list');

	def is_enabled(self, paths):
		return len(paths) == 1

class SideBarFilesRenameCommand(sublime_plugin.WindowCommand):
	def run(self, paths, newLeaf = False):
		branch, leaf = os.path.split(paths[0])
		self.window.run_command('hide_panel');
		self.window.show_input_panel("New Name:", newLeaf or leaf, functools.partial(self.on_done, paths[0], branch), None, None)

	def on_done(self, old, branch, leaf):
		new = os.path.join(branch, leaf)
		item = SideBarItem(old, os.path.isdir(old))
		try:
			if not item.move(new):
				sublime.error_message("Unable to rename, destination exists.")
				self.run([old], leaf)
		except:
			sublime.error_message("Unable to rename:\n\n"+old+"\n\nto\n\n"+new)
			self.run([old], leaf)
		self.window.run_command('refresh_folder_list');

	def is_enabled(self, paths):
		return len(paths) == 1
	
class SideBarFilesMoveCommand(sublime_plugin.WindowCommand):
	def run(self, paths, new = False):
		self.window.run_command('hide_panel');
		self.window.show_input_panel("New Location:", new or paths[0], functools.partial(self.on_done, paths[0]), None, None)

	def on_done(self, old, new):
		item = SideBarItem(old, os.path.isdir(old))
		try:
			if not item.move(new):
				sublime.error_message("Unable to move, destination exists.")
				self.run([old], new)
		except:
			sublime.error_message("Unable to move:\n\n"+old+"\n\nto\n\n"+new)
			self.run([old], new)
		self.window.run_command('refresh_folder_list');

	def is_enabled(self, paths):
		return len(paths) == 1

class SideBarFilesDeleteCommand(sublime_plugin.WindowCommand):
	def run(self, paths):
		self.window.run_command('hide_panel');
		self.window.show_input_panel("Delete:", paths[0], functools.partial(self.on_done, paths[0]), None, None)

	def on_done(self, old, new):
		self.remove(new)
		self.window.run_command('refresh_folder_list');
		
	def remove(self, path):
		if os.path.isfile(path) or os.path.islink(path):
			self.remove_safe_file(path)
		else:
			for content in os.listdir(path):
				file = os.path.join(path, content)
				if os.path.isfile(file) or os.path.islink(file):
					self.remove_safe_file(file)
				else:
					self.remove(file)
			self.remove_safe_dir(path)
	
	def remove_safe_file(self, path):
		if path != '' and path != '.' and path != '..' and path != './' and path != '/' and path != '//' and path != '\\' and path != '\\\\':
			try:
				os.remove(path)
			except:
				print "Unable to remove file:\n\n"+path

	def remove_safe_dir(self, path):
		if path != '' and path != '.' and path != '..' and path != './' and path != '/' and path != '//' and path != '\\' and path != '\\\\':
			try:
				os.rmdir(path)
			except:
				print "Unable to remove folder:\n\n"+path

	def is_enabled(self, paths):
		return len(paths) == 1


class SideBarFilesRevealCommand(sublime_plugin.WindowCommand):
	def run(self, paths):
		for item in SideBarSelection(paths).getSelectedItems():
			item.reveal()

	def is_enabled(self, paths):
		return len(paths) > 0