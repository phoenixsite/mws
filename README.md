# Multi-tenant Web Store
Multi-tenant Web Store. Downloadable services platform with a multi-tenant feature.

## Software requirements
The following list shows the software, and the corresponding version,
required to develop and execute the platform:

 - MongoDB (6.0)
 - Python (3.10.12)
 - [djongo](https://github.com/doableware/djongo) (1.3.6)
 - Django (4.2.3)

However, the latest version of djongo doesn't resolve
certain long-lasting problems, like some functionalities
in the Admin site or an [issue with the query operation
exists](htts://github.com/doableware/djongo/pull/647).
Because of this, it is included in this repo a modified
copy of the djongo package that may include some
modifications and must be installed using

    pip install ./djongo
    
before executing

    pip install -r requirements.txt
