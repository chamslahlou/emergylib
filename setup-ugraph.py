from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy

setup(
    ext_modules = cythonize((Extension("ugraph", sources=["ugraph.pyx"], include_dirs=[numpy.get_include()], ), )),
    zip_safe=False
)

