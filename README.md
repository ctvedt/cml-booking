# Django CML Booking

Simple django web app for booking time in an CML installation. Expect bugs, lots of bugs!

## Prerequisites

- An [CML](https://developer.cisco.com/docs/modeling-labs) installation
- An [SendMail](https://sendgrid.com/free/) account for sending out emails. Free works fine!

## Quick start for development installation

1. Clone repo  
```
git clone https://github.com/ctvedt/cml-booking.git
```

2. Move to cloned directory  
```
cd cml-booking/
```

3. Create and activate a Python Virtual Environment  
```
python -m venv venv
source venv/bin/activate
```

4. Install required pip packages  
```
pip install -r requirements.txt
```

5. Move to django web app directory  
```
cd django-cmlbooking
```

6. Copy the environment example file and edit this in your favorite editor  
```
cp .env.example .env
vim .env
```

7. Run the development web server  
```
./manage.py runserver
```

## Nice to know

The default account for the django admin page is `admin`, the password is `cmlbooking`. You should change this. Seriously.
