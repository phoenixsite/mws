# Multi-tenant Web Store
Multi-tenant Web Store. Downloadable services platform with a multi-tenant feature.

## Requirements
The following list shows the software required to execute the platform:

 - PostgreSQL 16 or newer:
 
 This should be installed on the database server. For development and testing purposes,
 it is recommended to set it up on the same machine as the Web server.
 
 - Python 3.11 or newer:
 
 Also it is required that all the Python packages in the requirements.txt file
 are installed.

## Installation instructions

### Database set up

1. PostgreSQL version 16 should be installed on a machine.
2. Create a user called 'mws_user' with some strong password on the PostgreSQL instance. In the following steps the password must be wrote on a file in the Django folder structure.
3. Create a database called 'mwsdb' whose owner is 'mws_user'.

### Platform set up

4. Clone the MWS source code with `git clone` or download the zip file from Github.
5. Create a file called 'mwsdb_password.txt' in the folder `src/mws/` of the Django project and write the 'mws_user' password on the previous file.
7. (Optional) Create a [virtual environment](https://docs.python.org/3/library/venv.html) on the project root folder.
8. (Optional) Activate the virtual environment.
9. Install the required packages using `pip install -r requirements.txt`.
10. If the database server is different from the one that executes the web server,
then the value of 'HOST' field of the 'src/mws/settings.py'
module and must be the IP address of the database server. If necessary, the 'PORT' field
must be also changed.
11. If you want some sample data to appear on the platform, you can execute in the 'src/' directory the command
`python manage.py populate_db`. 

## Running MWS

Once in the 'src/' directory, to run the server on the localhost is just necessary to execute `python manage.py runserver` and the
IP address and port of the web application will appear on screen. 