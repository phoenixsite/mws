# Multi-tenant Web Store
Multi-tenant Web Store. Downloadable services platform with multi-tenancy.

It is a platform where developers can register and start using the web store. 
They can publish their software packages so that their registered clients
can then download them. In addition, they can publish updates for 
specific packages and personalize the appearance of their store by 
modifying the footer fields and color theme.

This software is part of my final degree project from the degree
in Mathematics and Computer Science of the University of Granada, 
years 2018-2023.

## Requirements
The following list shows the software required to execute the platform:

 - PostgreSQL 16 or newer:
 
 This should be installed on the database server. For development and testing purposes,
 we set it up on the same machine as the Web server.
 
 - Python 3.11 or newer:
 
 Also it is required to install all the Python packages in the requirements.txt file.

## Installation instructions for a local set-up
The maximum number of tenants in this scenario is limited to five.

### Database set up

1. Install [PostgreSQL version 16](https://www.postgresql.org/download/).
2. Create a user called `mws_user` with some strong password on the PostgreSQL instance.
This user must have rights to create databases. In the following steps its password
must be wrote on a file in the Django folder structure.
3. Create a database called `mwsdb` whose owner is `mws_user`.

### Platform configuration

4. Clone the MWS source code with `git clone`.
5. Create a file called `mwsdb_password.txt` in the folder `src/mws/` of the Django
project and write the `mws_user` password on the previous file.
7. (Optional) Create a [virtual environment](https://docs.python.org/3/library/venv.html)
on the project root folder and activate it.
9. Install the required packages using `pip install -r requirements.txt`.
11. If you want some sample data to appear on the platform, you can execute in the
'src/' directory the command `python manage.py populate_db <ntenants>`.
12. This step needs to be made carefully. In order to make the web server accept
requests to some subdomains, which is the way the tenants are redirected to their
respective stores, we need to modify the host file of the operative system. Back it
up before proceeding.

   - If you are setting up the platform on Windows, you need to add the following
   lines to the file `C:\Windows\System32\drivers\etc\hosts`:
   ```
   127.0.0.1 mws.local
   127.0.0.1 tenant1.mws.local
   127.0.0.1 tenant2.mws.local
   127.0.0.1 tenant3.mws.local
   127.0.0.1 tenant4.mws.local
   127.0.0.1 tenant5.mws.local
   ```
   - If you are on an UNIX-based OS, you need to modify the file `/etc/hosts` by
   adding the following lines:
   ```
   127.0.0.1    mws.local
   127.0.0.1    tenant1.mws.local
   127.0.0.1    tenant2.mws.local
   127.0.0.1    tenant3.mws.local
   127.0.0.1    tenant4.mws.local
   127.0.0.1    tenant5.mws.local
   ```
   This is the reason why the number of tenants is limited to five, because
   we would need to modify the host file to add more tenants, something not yet
   implemented.

13. Finally, the last step is to migrate the models to the database created with
``python manage.py migrate``.

### Running MWS

Once in the `src/` directory, to run the server on the localhost is just necessary to
execute `python manage.py runserver` and the IP address and port of the web application
will appear on screen. 

## Performance testing and benchmarking
For testing the hypothetical performance of the platform, including its elasticity and scalability, 
we have used  [MuTeBench](https://github.com/MuTeBench/MuTeBench), a benchmarking 
framework for multi-tenant database systems. 

We have used a  virtual machine from the Department of Software Enginnering of the University of
Granada tp host the PostgreSQL 16 DBMS. This machine is configured with a Debian 11 "bullseye"
OS with 896.5 MB of RAM, 16 GB of storage and an Intel Core i7 9xx (Nehalem Class Core i7) with 
two 2.3 GHz cores and 16 MB of cache. All experiments were tested with such a virtual machine remotely.

We have designed four experiments to test the system in different situations. 

![Evolution plot of the first experiment](https://github.com/phoenixsite/mws/blob/main/1_agg_average.pdf)

