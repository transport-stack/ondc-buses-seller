# Setup of the seller app Latest

## Step1:
- Cloning the project (generate SSH Key on your system and add it to your profile on the code station)

  `git clone https://gitlab.com/chartrmobility/ondc/ondc-chartr-seller`
- Ask the project maintainer for the latest working branch and checkout to that branch.
- Once clone is done make a `./envs/.env.common` file copying from the `./envs/.env.common.sample` file
    ```bash
    cp ./envs/.env.sample ./envs/.env
    ```
- Ask the project maintainer for latest `.env.common` file
- Create `venv` and activate it
  ```bash
  python -m venv venv
  source venv/bin/activate
  ```
- Install packages and dependencies
  ```bash
  pip install -r requirements.txt
  ```
- Then run the command 
  ```bash
  export DJANGO_SETTINGS_MODULE=settings.development
  ```
## Step2:
- Run migrations 

  `python manage.py migrate`
- Create superUser

  `python manage.py createsuperuser`

## Step3:
- Start the app
- Run server

  `python manage.py runserver`


- Setup and start redis-server
- [Redis_setup](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/)

    ``
    redis-server
    ``


- Start celery worker in a new terminal
    ```
    export DJANGO_SETTINGS_MODULE=settings.development
    ```
    ```
    celery -A core worker --loglevel=info --pool=solo
    ```


- Start celery beat in a new terminal
    ```
    export DJANGO_SETTINGS_MODULE=settings.development
    ```
    ```
    celery -A core beat --loglevel=info
    ```

## Step4:
- Open Django admin `http://localhost:8000/admin/` and login with the superUser credentials. Now You should be able to see all the models.
- Open the `Ticket Types` table and add a type as `General`

## Step5:
- Ask the project maintainer for the `db.sqlite3` file and add it to the `data/fare_matrix` directory

## Step6:
- Now you can start working by creating a new branch for yourself
- Branch naming convention would be like `dev_<yourname>`
- `git checkout -b dev_<yourname>`



# ONDC Seller API Endpoints

## 2.1.1 Search (1)

**Objective:** Provide the user with all available stops and routes data.

**Description:**

* Returns every stop and its associated routes when no specific origin or destination is provided.
* Useful for fetching the complete network dataset.

---

## 2.1.2 Search (2)

**Objective:** Provide real-time bus search capabilities based on user queries.

**Description:**

* Accepts start and end stop parameters.
* Returns all possible routes connecting those stops, intermediate stops, fare details, and GPS coordinates.

---

## 2.1.3 Select

**Objective:** Allow users to select the route through which they want to travel.

**Description:**

* Manages user session state for route selection.
* Applies reservation timeout to release holds automatically.
* Returns the chosen route’s fare breakup and verifies the transaction session.

---

## 2.1.4 Init

**Objective:** Initiate bus ticket booking.

**Description:**

* Calculates total fare based on passenger count.
* Sends fare details to the buyer app to begin payment.
* Updates settlement terms if provided by the buyer.

---

## 2.1.5 Confirm

**Objective:** Confirm the bus ticket booking.

**Description:**

* Triggered after payment completion on the buyer side.
* Generates a PNR and returns a ticket (QR code) to the buyer.
* Supports multiple payment methods (UPI, credit/debit cards).

---

## 2.1.6 Update

**Objective:** Update an existing ticket booking.

**Description:**

* Accepts update requests from the buyer.
* Processes changes and returns the updated ticket details to the buyer.
