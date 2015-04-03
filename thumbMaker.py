import cuter as cut
import os,stat,sys

file_list=[]
def walktree(top, callback):
    """recursively descend the directory tree rooted at top, calling the
    callback function for each regular file. Taken from the module-stat
    example at: http://docs.python.org/lib/module-stat.html
    """
    for f in os.listdir(top):
        pathname = os.path.join(top, f)
        mode = os.stat(pathname)[stat.ST_MODE]
        if stat.S_ISDIR(mode):
            walktree(pathname, callback)
        elif stat.S_ISREG(mode):
            callback(pathname)
        else:
            print 'Skipping %s' % pathname

def addtolist(file, extensions=['.png', '.jpg', '.jpeg', '.gif', '.bmp']):
    """Add a file to a global list of image files."""
    global file_list  
    filename, ext = os.path.splitext(file)
    e = ext.lower()
    if e in extensions:
        if (file not in file_list):
            file_list.append(file)
    else:
        print 'Skipping: ', file, ' (NOT a supported image)'

if __name__ == '__main__':
	if len(sys.argv) > 1:
		walktree(sys.argv[1],addtolist)
		thumbdir=sys.argv[2]
		for file in file_list:
			filename,ext = file.replace(sys.argv[1],'').split('.')
			cut.resize_and_crop(file,thumbdir+'/'+filename+'_thumb.'+ext,[320, 240])