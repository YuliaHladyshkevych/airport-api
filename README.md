# Airport API 

API service for booking tickets and tracking flights from airports across the whole globe.

## Installing using GitHub
Install PostgresSQL and create db.

1. Clone the repository:
```bash
git clone https://github.com/YuliaHladyshkevych/airport-api
```
2. Navigate to the project directory:
```bash
cd airport_api
```
3. Switch to the develop branch:
```bash
git checkout develop
```
4. Create a virtual environment:
```bash
python -m venv venv
```
5. Activate the virtual environment:

On macOS and Linux:
```bash
source venv/bin/activate
```
On Windows:
```bash
venv\Scripts\activate
```
6. Install project dependencies:
```bash
pip install -r requirements.txt
```
7. Copy .env.sample to .env and populate it with all required data.
8. Run database migrations:
```bash
python manage.py migrate
```
9. Optional: If you want to prepopulate your database with some data, use:
```bash
python manage.py loaddata airport_db_data.json
```
10. Start the development server:
```bash
python manage.py runserver
```

## Run with Docker
Docker should be installed.

- pull docker container
``` 
docker pull yulia0904/airport_api
```
- run container
```
docker-compose up --build
```

## Getting access
* create user via /api/user/register/
* get access token via /api/user/token/
* look for documentation via /api/doc/swagger/
* admin panel via /admin/

## Features
* JWT Authentication
* Email-Based Authentication
* Admin panel
* Throttling Mechanism
* API documentation
* Creating airplane with Image
* Filtering for Flights and Routs
* Managing orders and tickets
* Implement a new permission class 
