# assayLoader: QC of assay raw data and loading curated data into Scarab

## Requirements
Required package versions listed in `requirements.txt`. Install the required versions with your favourite package manager.

## Frontend
### PyInstaller How-To
Currently builds on `Python` with required package versions listed in `requirements.txt`.
With `frontend` as current directory, build the main assayLoader executable with:

    <pyinstaller> main.spec
    python -m PyInstaller main.spec

which will build the main executable `al`(.exe)
</br>or

    <pyinstaller> launcher.spec
    py -m PyInstaller launcher.spec

which will build the launcher executable `assayLoader`(.exe).

Substitute `<pyinstaller>` with your local appropriate PyInstaller module (possibly `py -3.8 -m PyInstaller` or just `python3 pyinstaller`, case sensitive module names).

<b> Make sure to build a new version of the `ce` executable before using `upload.py` to upload a new version.
</b>

### Using `upload.py`

Invoking `python3 upload.py` should give the following output:
    
    $ .../assayLoader/frontend$ python3 upload.py
    Please specify path(s) to executables and/or version data files
    -t <path>: path to main executable
    -v <path>: path to version data file
    -l <path>: path to launcher executable

To use `upload.py`, use these options to provide files to upload.

If you have built the main executable and launcher from the /frontend directory using *pyinstaller*, sample usage would look like this:

    python upload.py -t dist/al.exe -l dist/assayLoader.exe

Invoking this prompts a login verification from the server, after which the files are sent to the server.


## Backend

## Download Launcher
To download the launcher executable from the server, navigate to:

    <baseUrl>getAssayLoaderLauncher/Windows/assayLoader.exe
    <baseUrl>getAssayLoaderLauncher/Linux/assayLoader
    <baseUrl>getAssayLoaderLauncher/Darwin/assayLoader
    Ex:
    http://esox3.scilifelab.se:8084/getAssayLoaderLauncher/Windows/assayLoader.exe


using your favourite internet browser.
