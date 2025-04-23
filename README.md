# youtube-dl-microservice
Simple REST microservice written in Flask that can download YouTube videos locally to your machine. Outputs YouTube videos as mp4 or mp3 files.

## Prerequisites
- Python (https://www.python.org/)
- pip (https://pip.pypa.io/en/stable/)
    - package manager for Python libraries
    - **Note:** If you have Python version 3.4 or later, pip is included by default.
- FFmpeg (https://www.ffmpeg.org/) to merge streams (audio + video) together 
- Postman (https://www.postman.com/) or **curl** (https://curl.se/) to invoke APIs

## Required packages that will be installed with virtual environment and pip
- Flask (https://pypi.org/project/Flask/)
- pytubefix (https://pypi.org/project/pytubefix/)

## Usage
1. Download/clone the repository to your local machine: `git clone https://github.com/phoang7/youtube-dl-microservice.git`
2. Change current directory to `youtube-dl-microservice` repository: `cd <path_to_youtube_dl_microservice_repostiory>`
3. Create a new virtual environment and activate it with `venv` module (https://docs.python.org/3/tutorial/venv.html#creating-virtual-environments)
4. Once virtual environment is activated, run the pip command to install the required packages: `pip install -r requirements.txt`
5. You can then run the microservice with the following command: `python services\youtube_dl.py`
6. **[Optional]** If you would like to set a destination directory to download Youtube videos as mp4 or mp3 files to, run the following command instead: `python services\youtube_dl.py -dest <path_to_destination_dir>`, otherwise the destination directory will be set to the current working directory by default.
7. To exit microservice, in terminal or command prompt where service is running, perform input `Ctrl + C`.

## API Doc
See `api-doc.yaml` to view API documentation.

## Can I run this service in Docker?
Yes, make sure to replace the value `/your_volume_path` in `compose.yaml` with the value of the absolute path on your client/machine where you want YouTube files to be downloaded to. Also make sure to include the port in the url when invoking APIs. The default port is `8000`.

## Can I use a newer or older release of pytubefix?
pytubefix is not maintained by me. Use the version or release that works best for you!