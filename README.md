Compiling the HGSF-Aware PyPy
-----------------------------
The patch only works with pypy2-v5.8 since that is the version we used
during DAC submission. Download the PyPy source, patch it with this
pypy-patch.txt, and compile it with either prebuilt PyPy (takes 20-40
minutes) or CPython (3 hours) using the following command. Refer to this
page as well.

```
$ wget https://bitbucket.org/pypy/pypy/downloads/pypy2-v5.8.0-src.tar.bz2
$ tar -xvf pypy2-v5.8.0-src.tar.bz2
$ cd pypy2-v5.8.0
$ patch -p1 < pypy-patch.txt
$ cd pypy/goal
$ <python/pypy> ../../rpython/bin/rpython \
   --translation-jit_opencoder_model big -Ojit targetpypystandalone
```

Setup virtualenv
----------------
Mamba is only tested to work with Python2 (Python 2.7 is recommended).

**Mamba simulation should work out-of-the-box with the default CPython on
Linux without extra packages.**


We highly recommend using a virtual environment to avoid problems. Note
that you may set up virtualenv for both CPython and PyPy for performance
comparison. You just need to install pytest, cffi, and graphviz in the
virtualenv. We list the commands under ubuntu linux.

```
$ sudo apt-get install virtualenv
$ virtualenv --python=<pypy/goal/pypy-c or just python> <folder-for-venv>
$ source <folder-for-venv>/bin/activate
```

"Installing" Mamba framework
----------------------------
Mamba is a new version of pymtl, and is included in mamba/. Currently we
don't install it; we just add mamba/ folder to PYTHON_PATH in simulator or
conftest. You don't need to do much if you want to run the divider
experiments

The following should work out-of-the-box.

```
$ cd divider/mamba
$ ./idiv-sim --help
$ ./idiv-sim --trace
```
