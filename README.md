# Multi-tenant Web Store
Multi-tenant Web Store. Downloadable services platform with a multi-tenant feature.

## Requirements
The following list shows the software required to execute the platform:

 - PostgreSQL 16 or newer:
 
 This should be installed on the database server. For development and testing purposes,
 we set it up on the same machine as the Web server.
 
 - Python 3.11 or newer:
 
 Also it is required to install all the Python packages in the requirements.txt file.

## Installation instructions for a local set-up

### Database set up

1. Install [PostgreSQL version 16](https://www.postgresql.org/download/).
2. Create a user called `mws_user` with some strong password on the PostgreSQL instance.
This user must have rights to create databases. In the following steps its password
must be wrote on a file in the Django folder structure.
3. Create a database called `mwsdb` whose owner is `mws_user`.

### Platform set up

4. Clone the MWS source code with `git clone` or download the zip file from Github.
5. Create a file called `mwsdb_password.txt` in the folder `src/mws/` of the Django
project and write the `mws_user` password on the previous file.
7. (Optional) Create a [virtual environment](https://docs.python.org/3/library/venv.html)
on the project root folder and activate it.
9. Install the required packages using `pip install -r requirements.txt`.
11. If you want some sample data to appear on the platform, you can execute in the
'src/' directory the command `python manage.py populate_db <ntenants>`. 

## Running MWS

Once in the `src/` directory, to run the server on the localhost is just necessary to
execute `python manage.py runserver` and the IP address and port of the web application
will appear on screen. 