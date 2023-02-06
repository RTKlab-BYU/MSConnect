<h1 style="text-align: center;">
Proteomic Data Manager
</h1>

Proteomic Data Manager is a Web-based, flexible, open-source platform for automated high-throughput MS-based omics. This platform supports a variety of existing tools, allowing for a fully autonomous workflow from data collection to data backup, processing with different 3rd party software, and finally generating tables and figures for data visualization.  The program is built mainly on Python Django framework, along with Javascript, and HTML. It works with [Raw file uploader](https://github.com/RTKlab-BYU/Raw_File_Uploader) and [Processor](https://github.com/RTKlab-BYU/Proteomics_Data_Processor).


## key features of platform include:
1. Automated raw file upload with meta data from instrument control PCs in a vendor-independent fashion.
2. User-configurable, automated, redundant data backup and purging. 
3. Automated and distributed data processing using various 3rd party software kits that support command line. 
4. Easy installation with Docker container-based deployment and simple integration of other 3rd party Docker images.
5. A SQL database linked data structure that allows users to search data and files through a web interface or programmatically.
6. Integration of the Django REST framework for API access and Jupyter Notebook for scripting with Python and R. 
7. An app-store style module distribution system between developers and users.

### How to install or depoly
The easiest way to depoly the platform is through Docker compose, make sure Docker compose is properlly installed [official guide](https://docs.docker.com/compose/install/)
 1. Download the repository to your local folder
 2. Change .django_secrets.env_example to .django_secrets.env, and configure .django_secrets.env and docker-compose.yml. see the [wiki page](https://github.com/RTKlab-BYU/Proteomic-Data-Manager/wiki).
 3. Start the app through "docker compose up" or other approaches


### Documentation
For technical documentation on platform (hardware requirements, configuration parameters, etc.), see the [wiki page](https://github.com/RTKlab-BYU/Proteomic-Data-Manager/wiki).



### Requests for Collaboration
If you would like to propose a new collaboration or participate in the development or development nodes, please just submit a request or contact us directly. 

### screenshoots
![dashboard](https://user-images.githubusercontent.com/77813931/217036159-7bcc1e1c-e11c-4495-8cf7-ee797b3c83f7.PNG)![UI](https://user-images.githubusercontent.com/77813931/217036175-6988f010-5114-4f1d-aa2f-5f0e1bf532a1.PNG)


