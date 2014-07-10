PostgreSQL Shepherd - Innovative Project
==========

|                  | PostgreSQL Shepherd          | 
| ---------------- | ------------- | 
| Project goals    | Single application for multiple PostgreSQL instances managing | 
| Scope definition | Functionalities: copying database or schema between instances, copying roles, executing queries in parallel |   
| Requirements     | Python      |   
| Idea author      | Wojciech Stachowski     |   

Instalation
--

    run install.py script in install folder
    install.py includes libraries for py3.3 64bit
    
Windows service ssh-shepherd
--
    run "ssh-shepherd-svc.py install"
    NET START ssh-shepherd-svc

Libraries
--
    pyyaml
    paramiko
    psycopg2
    pywin32
    libkeepass
    pycrypto
    prettytables
    
Warning
--
    To be able to use ssh tunnels you have to run ssh-shepherd