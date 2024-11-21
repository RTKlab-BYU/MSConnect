<h1 style="text-align: center;">
MSConnect
</h1>

MSConnect is a Web-based, flexible, open-source platform for automated high-throughput MS-based omics. This platform supports a variety of existing tools, allowing for a fully autonomous workflow from data collection to data backup, processing with different 3rd party software, and finally generating tables and figures for data visualization. The platform is built with Python Django, JavaScript, and HTML and works with [Raw file uploader](https://github.com/RTKlab-BYU/Raw_File_Uploader) and [Processor](https://github.com/RTKlab-BYU/Proteomics_Data_Processor). 

<h4>Please note: while the platform supports all 3rd party applications, they are not included and licensing requirements should be consulted with their respective owners.</h4>

![drawing_smaller](https://user-images.githubusercontent.com/77813931/217049351-eab79f9a-9c97-4c17-9ed8-cfb0f9bd660d.png)


## Key features of platform include:
1. Automated upload of raw files and meta data from instrument control PCs, regardless of manufacturer.
2. User-configurable, automated, redundant data backup and purging. 
3. Automated and distributed data processing using various 3rd party software kits that support command line. 
4. Easy installation with Docker container-based deployment and simple integration of other 3rd party Docker images.
5. A SQL database linked data structure that allows users to search data and files through a web interface or programmatically.
6. Integration of the Django REST framework for API access and Jupyter Notebook for scripting with Python and R. 
7. A module distribution system between developers and users similar to an app-store.


## Documentation
For technical documentation on the platform, including hardware requirements and configuration parameters, see the [wiki page](https://github.com/RTKlab-BYU/Proteomic-Data-Manager/wiki).


## Requests for Collaboration
To propose new collaborations or participate in development, submit a request or contact us directly ryan.kelly@byu.edu.


## How to cite
If you use MSConnect for your work, we request that you cite MSConnect in relevant papers. A manuscript is currently being prepared and will be available soon.


## Screenshots
![dashboard](https://user-images.githubusercontent.com/77813931/217036159-7bcc1e1c-e11c-4495-8cf7-ee797b3c83f7.PNG)![UI](https://user-images.githubusercontent.com/77813931/217036175-6988f010-5114-4f1d-aa2f-5f0e1bf532a1.PNG)


## Table of Contents
**[Installation](#installation)**<br>
**[Accessing the App](#access-app)**<br>
**[Page Organization](#raw-data-formats)**<br>
**[Dashboard Page](#spectral-library-formats)**<br>
**[Visualization Page](#output)**<br>
**[Processing Page](#library-free-search)**<br>
**[Record Page](#creation-of-spectral-libraries)**<br>
**[Settings Page](#match-between-runs)**<br>
**[Advanced Page](#changing-default-settings)**<br>
**[App Center](#command-line-tool)**<br>
**[Django Admin Page](#visualisation)**<br>
**[Frequently Asked Questions (FAQ)](#automated-pipelines)**<br>
**[Support](#ptms-and-peptidoforms)**<br>


## <a id="installation">Installation</a>
Deploying the platform involves three simple steps and typically takes less than 20 minutes (detailed instructions are available on the [wiki page](https://github.com/RTKlab-BYU/MSConnect/wiki/Installation)):
 1. Install Docker by following the [official guide](https://docs.docker.com/compose/install/).
 2. Download the repository to your local folder. Configure the docker-compose.yml and .django_secrets.env files to specify the file storage location and make other optional settings.
 3. Start the app with "docker compose up".


## <a id="access-app">Accessing the App</a>
### 1. Gaining Access
By default, there are two accounts created preinstalled with the software.

**Admin Account** - intended for application management. It's recommended to change the password for this account via the admin site (under help/admin) once the application is deployed.
```
Username: admin   Password: proteomicsdatamanager
```
**Generic Account** - standard user account, intended for database searching. Unless there are security concerns, this account can be left as is.
```
Username: search_worker   Password: searchadmin
```
### 2. Access the app
there are two ways to access the application, It can be accessed on the device that it was installed on or it can be accessed over the internet.

* **Accessing the application locally**
     After installation, it's a good idea to first access the application locally to ensure proper installation. Users can access locally (on the same installed system) by typing ["localhost"](http://localhost/) into your browser's address bar. A login screen should appear, then you can use the above default admin account or create a new account to access the application.
   
* **Accessing the application through the network**
     Instead of putting the localhost in the browser's address bar, you need to put the IP address of the server (where the application is installed. Find the IP address of a PC through, [Windows IP address](https://support.microsoft.com/en-us/windows/find-your-ip-address-in-windows-f21a9bbc-c582-55cd-35e0-73431160a1b9), [Linux IP address](https://www.abstractapi.com/guides/linux-get-ip-address), [Mac IP address](https://www.wikihow.com/Find-Your-IP-Address-on-a-Mac)

If you encounter any errors, refer to the [troubleshooting page](https://github.com/RTKlab-BYU/Proteomic-Data-Manager/wiki/Troubleshootings) for potential solutions and advice.


### What's Next? 
* [How to Navigate through the app](https://github.com/RTKlab-BYU/Proteomic-Data-Manager/wiki/Page-Organization),
* [How to upload your raw file](https://github.com/RTKlab-BYU/Raw_File_Uploader/wiki)
* [How to set up automated processing](https://github.com/RTKlab-BYU/Raw_File_Uploader/wiki/How-to-set-up-Auto%E2%80%90Uploading)

### Figure 1: What the website looks like after being properly installed.
![image](https://github.com/RTKlab-BYU/Proteomic-Data-Manager/assets/77813931/418ba6d7-1bf1-450d-bcdd-c88c0f87eb65)
 
