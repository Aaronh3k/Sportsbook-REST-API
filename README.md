# Sports-Book-REST-API-Service

Welcome to the Sports-Book-Management-API, a Flask-based RESTful service designed to assist sports enthusiasts and organizations in effectively managing their sporting events, selections, and sports types. Inspired by leading sports management applications, this service aims to streamline the process of creating, updating, fetching, and deleting sports-related information.

At its core, this service provides the following features:

- **Sport Management:** Add, update, and retrieve detailed information about various sports, each uniquely identified for easy access.
- **Event Management:** Efficiently manage your sporting events with essential attributes like type (preplay or inplay), status (Pending, Started, Ended, Cancelled), and related sport.
- **Selection Management:** Within each event, handle the selections with attributes like price, activity status, and potential outcomes (Unsettled, Void, Lose, Win).
- **External Sports Data Integration:** Seamlessly fetch and store sports data, selections data, and events data from third-party sources using the Odds API. This allows the service to remain updated with real-time data from bookmakers worldwide, enhancing the accuracy and richness of available information.

The service is backed by a robust SQL database structure ensuring the reliability of the service.

Take a peek at the tree structure below to understand the project organization:

```plaintext
.
├── alembic
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions
│       ├── bc150950f793_add_trigger_to_update_active_status_of_.py
│       ├── fee927264e0a_create_initial_tables.py
│       └── __pycache__
├── alembic.ini
├── README.md
├── requirements.txt
├── run.py
├── src
│   ├── app.py
│   ├── config
│   ├── controllers
│   ├── helpers.py
│   ├── libs
│   └── models
└── static
    └── swagger.yml
```

## Getting Started

Here's a quick guide on how to get the Sports-Book-REST-API-Service up and running on your local machine for development and testing purposes.

### Prerequisites

The following tools are required to setup and run this project:

- **Python:** The application is built with Python. Make sure you have Python version 3.9.0 or above. You can download it from [here](https://www.python.org/downloads/).

- **Flask:** The application uses Flask as a web framework. It will be installed when setting up the project.

- **Pip:** Pip is a package management system used to install and manage software packages written in Python. Usually, it's installed with Python. If not, you can install it from [here](https://pip.pypa.io/en/stable/installing/).

### Installation

Please follow these steps to install the application and its dependencies:

**Step 1:** Clone this repository to your local machine using:

```bash
git clone https://github.com/Aaronh3k/Sportsbook-REST-API.git
```

**Step 2**: Navigate to the project directory:

```bash
cd Sportsbook-REST-API
```

**Step 3**: Install the required Python dependencies:

```bash
pip install -r requirements.txt
```

**Step 4**: Run the application:

```bash
./run.py
```

# API Functionality

This API facilitates efficient management of sports, events, and selections with several distinct features:

- **Sports, Events, and Selections Management:** The API allows the creation, retrieval, update, and deletion of sports, events, and selections data. Users can create new entries through a POST request, fetch details through GET requests, which support various filtering, sorting, and regex search mechanisms, update specific details through a PATCH request, and remove entries permanently using a DELETE request.

- **Integration with External APIs:** Unique to this API is its capacity to interact with external APIs for sports and selections data. It fetches data related to a specific sport or event and stores it in the database, offering flexibility in terms of the volume of data integration.

- **Comprehensive Data Structure:** Each object - sport, event, or selection - comprises attributes that provide detailed information, such as names, URL identifiers, active status, scheduled start and actual start times for events, and pricing information for selections.

This API stands as a comprehensive tool designed for effective management and integration of sports, events, and selections data, ensuring robust control over all related needs.

## Database Schema

# Deployment Process

This API leverages the robust capabilities of AWS to ensure scalable, efficient, and reliable deployment. Two Amazon Web Services' tools are utilized to create a smooth-running system:

- **AWS Elastic Beanstalk:** The main application is hosted and managed on AWS Elastic Beanstalk, offering automated deployment of applications in the cloud, significantly simplifying the process.

- **Amazon RDS (PostgreSQL):** Serving as the backbone for the API's database, Amazon RDS with PostgreSQL engine is used. This offers a secure and scalable database environment that's easy to set up, operate, and scale.

To understand the deployment process and the interplay of these services better, an architectural diagram is included in the repository. It offers a comprehensive visual representation of how these services work in synergy to provide a reliable and efficient API.

# Continuous Integration/Continuous Deployment (CI/CD)

The API adopts a CI/CD pipeline through GitHub Actions to automate the building, and deployment process. The workflow, named "Sports Book Service CI/CD", is triggered every time there is a push to the `master` branch.

The pipeline is designed to run on an `ubuntu-latest` environment and performs a series of actions:

1. **Code Checkout:** The repository is checked out using `actions/checkout@v2`.

2. **Python Setup:** Python 3.9 is set up using `actions/setup-python@v2`.

3. **Dependency Installation:** All required dependencies are installed with pip.

4. **Deployment Package Creation:** Upon successful execution of the tests, a deployment package is created excluding any `.git`, `__pycache__`, and `tests` files/directories.

5. **Deployment to Elastic Beanstalk:** The deployment package is then deployed to AWS Elastic Beanstalk using `einaregilsson/beanstalk-deploy@v14`. This action is performed with the AWS access key and secret key stored as GitHub Secrets to ensure secure access.

This CI/CD workflow allows for reliable, efficient, and secure software delivery by automating the entire process of integration, testing, and deployment.

# API Documentation

## Postman Collection

To make it easier to test the API endpoints, a Postman collection is provided. Postman is an API testing tool that allows you to send different HTTP requests to the API. You can use the collection to send requests to our API and observe the responses.

Access the Postman collection [here](https://documenter.getpostman.com/view/5044011/2s946ibWsB).

## Swagger Documentation

The API also comes with a comprehensive Swagger documentation that provides details about all the available endpoints, their expected parameters and responses, and possible status codes and their meanings. This documentation can be of great help when trying to understand what functionality is available and how to use it.

Access the Swagger documentation [here](http://sports-book.us-east-1.elasticbeanstalk.com/v1/api/docs/).

# Access the API

Interact with the API directly using the base URL provided below. Remember to include the `/v1/` suffix to ensure the use of version 1 of the API:

[here](http://sports-book.us-east-1.elasticbeanstalk.com/v1/)
