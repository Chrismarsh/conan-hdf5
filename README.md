# hdf5

This is a minimal Conan build of the hdf5 library for use with [CHM](https://github.com/Chrismarsh/CHM). 

Build artifacts are uploaded to [Bintray](https://bintray.com/chrismarsh/CHM)


```
conan install hdf/1.10.5@CHM/stable
```

## Executables and shared libraries

When the package is compiled with the `shared=True` option, the _rpath_ for
executables is set to _$ORIGIN/../lib_ on Linux and _@executable_path/../lib_
on macOS.


## Parallel HDF5

Parallel libraries can be compiled with the `parallel=True` option, **but in
this case the C++ libraries are not compiled**. This option requires MPICH and
assumes the C and C++ compilers are available on the path as _mpicc_ and
_mpic++_. If this is not the case, the compilers can be set using the _CC_ and
_CXX_ environment variables, respectively. Tested with _mpich-3.2-devel_
installed with yum on CentOS 7 and _mpich_ installed with MacPorts on macOS.
