# pyramid-focus-stack
This program implements a modified version of the focus stacking algorithm based on Laplacian pyramids, described by Wang and Chang, doi:10.4304/jcp.6.12.2559-2566. A simple gui is provided to facilitate use by regular photographers. The routine has been tested on Windows 10/11 as well as Ubuntu Linux 24.4. It should work on other Linux flavours with minimal changes.
## Installation - Linux
Unpack the code to any convenient directory. Open a command window and `cd` to the code location. Many Linux distributions enforce use of a virtual environment when installing libraries; in any case, use of a virtual environment is recommended. Generate and activate the environment, and then install the necessary libraries:

	python -m venv env  
	source env/bin/activate
	pip install PySide6
	pip install opencv-python
It should now be possible to start the program by running

	python stacker_mainwindow.py
Some Linux distributions including Ubuntu require you to use `python3` instead of `python` in the above commands.
If you use the program frequently, you may want to start it by double-clicking an icon as usual. Consult your distro documentation on how to do this. In Ubuntu, modify `focus_stack.sh` according to your own file location and user name. Note this batch file activates the virtual environment before running the python program. Also modify the focus.desktop file in the same way. This desktop file should be saved to the

	/home/<your username>/.local/share/applications
directory.

## Installation - Windows 11
On Windows, Python should be installed as a first step. Look for Python on the Microsoft store, and install the latest stable version. Once this is done, open a command shell window. Under Windows, use of a virtual environment is not enforced: these instructions assume one is not used.

Issue the following commands in the shell window

	pip install Pyside6
	pip install opencv-python

Now download the project files to a suitable directory.
## Using the program
Input to the program is a directory location containing a number of images which form a focus stack. The program will stack together all the images in the directory into a single output image retaining the best-focussed example of each point in the scene. All the images must be the same size and may be in 8 or 16 bit resolution per colour channel in a common format such as .png or .jpg. Raw image formats are not supported. Select the input directory either by editing the text box, or through the menu File -> Select input path option. If necessary, change the output file after choosing the input.

The default input and output locations can be changed by editing the init.txt file, which is written the first time the program is run.

Various parameters can be changed to affect the running of the program. The energy filter size determines how large an area is used to detemine how in-focus each input image is, at each point.
The stack method allows the focus assessment to be made, either on a grayscale version of the image, or separately determined and applied to each colour channel.
The pyramid stacking method, when applied to a series of images, can yield a small number of pixel values which lie outside the valid range. Such values can either be clipped to their respective minimum or maximum, or all the values can be scaled to fit within the valid range. In practice, the performance changes caused by changing these parameters tends to be small.
