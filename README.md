<h1 style="text-align: center;">
$${\color{green} MSConnect}$$

</h1>

MSConnect is a Web-based, flexible, open-source platform for automated high-throughput MS-based omics. It streamlines the entire process from data collection, data management, data processing and to data visualization by integrating and supporting various third-party tools, allowing for a fully autonomous. The platform is built with Python, Django, JavaScript, and HTML and works with [Raw file uploader](https://github.com/RTKlab-BYU/Raw_File_Uploader) and [Processor](https://github.com/RTKlab-BYU/Proteomics_Data_Processor). 

<h4>Please note: while the platform supports all 3rd party applications, they are not included and licensing requirements should be consulted with their respective owners.</h4>

![Overview](https://github.com/user-attachments/assets/de0d6160-e8a7-4289-bd99-753ad46c69dd)

## $${\color{green} What \space It \space Does }$$
MSConnect is a comprehensive platform that automates the following tasks:  
- Data Management: Streamlines the uploading and organization of raw MS files.
-	Data Backup: Provides secure storage throughout the processing pipeline.
- Data Processing: Interfaces with third-party tools to analyze MS raw data.
-	Result Interpretation: Generates tables and figures for easy interpretation and presentation of results.  

## $${\color{green} Key \space features \space of \space platform \space }$$
-	Vendor-Independent: Compatible with diverse MS applications, ensuring flexibility across platforms.
-	Automation: Offers fully autonomous workflows, minimizing manual intervention.
-	User-configurable, automated, redundant data backup and purging. 
-	Third-Party Integration: Seamlessly connects with external software for advanced analysis.
- Visualization Tools: Provides clear and actionable data representations for streamlined interpretation (depends on user workflow may required 3rd party modules).
-	Generalized Framework: Adaptable to various omics studies, expanding its applicability.
-	Easy installation with Docker container-based deployment and simple integration of other 3rd party Docker images.
- A SQL database linked data structure that allows users to search data and files through a web interface or programmatically.
-	A module distribution system between developers and users similar to an app-store.
-	Integration of the Django REST framework for API access and Jupyter Notebook for scripting with Python and R. 

## $${\color{green}  What \space It \space Is \space Not }$$

-	MSConnect is not a standalone data analysis tool. It depends on third-party software for data processing/analysis
- MSConnect does not come with any data processor or analysis software/license, it provides a wrapper/interface to interact with them.  
- It is not limited to any specific MS application; instead, it provides a generalized framework adaptable to various omics studies.  
-	MSConnect is not a desktop application; it is web-based and requires a server (can be an old PC) for deployment (using Docker to enable fast deployment in less than 30 min). 



## $${\color{green} Documentation }$$

Download [User Manual](https://github.com/user-attachments/files/18134289/MSconnect_UserManual_Lav_1213_clear.pdf) or visit MSConnect wiki page [wiki page](https://github.com/RTKlab-BYU/Proteomic-Data-Manager/wiki).

## $${\color{green} What \space You \space Need (Requirements}$$

- PC computer less than 10 years old (linux, unix, windows) 
8 gigs of Ram, 120 gig storage, 
- Third-party software for specific MS data analysis tasks. (sofware requirements)
- Ability to set up processing workflow to enable auto processing by following the tutorial. [Processing module/wrapper setup](https://github.com/RTKlab-BYU/MSConnect/wiki/How-to-Setup-Procssing-Modules)

## $${\color{green} Requests \space for \space Collaboration }$$
To propose new collaborations or participate in development, submit a request or contact us directly ryan.kelly@byu.edu.

## $${\color{green} How \space to \space cite }$$

If you use MSConnect for your work, we request that you cite MSConnect in relevant papers. A manuscript is currently being prepared and will be available soon.



 
