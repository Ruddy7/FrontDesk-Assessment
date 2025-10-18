Clone this repository and make a .env file which should look like this <br>
<br>
LIVEKIT_URL= your project url <br>
LIVEKIT_API_KEY= your livekit api key <br>
LIVEKIT_API_SECRET= your livekit api secret <br><br>

The .env should be in root folder.
<br><br>
Now either make a virtual environment(Prefered) and install all the packages or just run the command to directly install them on your global environment.<br>
To make a virtual environment,<br>
first type **python -m venv venv** or **python3 -m venv venv** in your terminal<br>
followed by **.\venv\Scripts\activate**, which activates your virtual environment.<br>
<br>
The command to install the required packages is **pip install -r requirements.txt** <br><br>

Lastly, you just need to type **deactivate** in your terminal to deactivate the Virtual environment and start using your global environment again. <br>
However, to use this virtual environment again, you need to type the same command in your terminal which is **.\venv\Scripts\activate**
