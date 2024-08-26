<h1 style="text-align: center;">
MSConnect
</h1>

MSConnect is a Web-based, flexible, open-source platform for automated high-throughput MS-based omics. This platform supports a variety of existing tools, allowing for a fully autonomous workflow from data collection to data backup, processing with different 3rd party software, and finally generating tables and figures for data visualization.The platform is built with Python Django, JavaScript, and HTML and works with [Raw file uploader](https://github.com/RTKlab-BYU/Raw_File_Uploader) and [Processor](https://github.com/RTKlab-BYU/Proteomics_Data_Processor). 

<h4>Please note: while the platform supports all 3rd party applications, they are not included and licensing requirements should be consulted with their respective owners.</h4>

![drawing_smaller](https://user-images.githubusercontent.com/77813931/217049351-eab79f9a-9c97-4c17-9ed8-cfb0f9bd660d.png)


## Key features of platform include:
1. Automated raw file upload with meta data from instrument control PCs in a vendor-independent fashion.
2. User-configurable, automated, redundant data backup and purging. 
3. Automated and distributed data processing using various 3rd party software kits that support command line. 
4. Easy installation with Docker container-based deployment and simple integration of other 3rd party Docker images.
5. A SQL database linked data structure that allows users to search data and files through a web interface or programmatically.
6. Integration of the Django REST framework for API access and Jupyter Notebook for scripting with Python and R. 
7. An app-store style module distribution system between developers and users.

## Installation or Deployment Guide
Deploying the platform involves three simple steps and typically takes less than 20 minutes (detailed instructions are available on the [wiki page](https://github.com/RTKlab-BYU/Proteomic-Data-Manager/wiki/How-to-install)):
 1. Install Docker by following the [official guide](https://docs.docker.com/compose/install/).
 2. Download the repository to your local folder. Configure the docker-compose.yml and .django_secrets.env files to specify the file storage location and make other optional settings.
 3. Start the app with "docker compose up".


## Documentation
For technical documentation on the platform, including hardware requirements and configuration parameters, see the [wiki page](https://github.com/RTKlab-BYU/Proteomic-Data-Manager/wiki).



## Requests for Collaboration
To propose new collaborations or participate in development, submit a request or contact us directly ryan.kelly@byu.edu.

## How to cite
If you use MSConnect for your work, we request that you cite MSConnect in relevant papers. A manuscript is currently being prepared and will be available soon.
## Screenshoots
![dashboard](https://user-images.githubusercontent.com/77813931/217036159-7bcc1e1c-e11c-4495-8cf7-ee797b3c83f7.PNG)![UI](https://user-images.githubusercontent.com/77813931/217036175-6988f010-5114-4f1d-aa2f-5f0e1bf532a1.PNG)


