# Ingests user profile data from DummyJSON REST API
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import csv
import random
from datetime import datetime, timedelta
from ingestion.logger_config import get_logger

logger = get_logger(__name__)

# Sample data for generating realistic demographics
FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa", "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley", "Steven", "Dorothy", "Paul", "Kimberly", "Andrew", "Emily", "Joshua", "Donna", "Kenneth", "Michelle", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa", "Edward", "Deborah", "Ronald", "Stephanie", "Timothy", "Rebecca", "Jason", "Laura", "Jeffrey", "Sharon", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy", "Nicholas", "Shirley", "Eric", "Angela", "Jonathan", "Helen", "Stephen", "Anna", "Larry", "Brenda", "Justin", "Pamela", "Scott", "Nicole", "Brandon", "Emma", "Benjamin", "Samantha", "Samuel", "Katherine", "Gregory", "Christine", "Frank", "Debra", "Alexander", "Rachel", "Raymond", "Catherine", "Patrick", "Carolyn", "Jack", "Janet", "Dennis", "Ruth", "Jerry", "Maria", "Tyler", "Heather", "Aaron", "Diane", "Jose", "Virginia", "Adam", "Julie", "Henry", "Joyce", "Nathan", "Victoria", "Douglas", "Olivia", "Zachary", "Kelly", "Peter", "Christina", "Kyle", "Lauren", "Walter", "Cynthia", "Ethan", "Marie", "Jeremy", "Ann", "Harold", "Jean", "Christian", "Alice", "Keith", "Doris", "Noah", "Abigail"]

LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts"]

CITIES = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville", "Fort Worth", "Columbus", "Charlotte", "San Francisco", "Indianapolis", "Seattle", "Denver", "Washington"]

STATES = ["California", "Texas", "New York", "Florida", "Illinois", "Pennsylvania", "Ohio", "Georgia", "North Carolina", "Michigan"]

GENDERS = ["male", "female"]
BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
EYE_COLORS = ["Brown", "Blue", "Green", "Hazel", "Gray", "Amber"]
HAIR_COLORS = ["Black", "Brown", "Blonde", "Red", "Gray", "White"]
HAIR_TYPES = ["Straight", "Wavy", "Curly", "Kinky", "Coily"]

UNIVERSITIES = ["Harvard University", "Stanford University", "Massachusetts Institute of Technology", "University of California, Berkeley", "Yale University", "Princeton University", "Columbia University", "University of Chicago", "California Institute of Technology", "University of Pennsylvania"]

DEPARTMENTS = ["Engineering", "Marketing", "Sales", "Human Resources", "Finance", "Operations", "Research and Development", "Customer Support", "Product Management", "Legal"]

TITLES = ["Software Engineer", "Marketing Manager", "Sales Representative", "HR Specialist", "Financial Analyst", "Operations Manager", "Research Scientist", "Support Specialist", "Product Manager", "Legal Counsel"]

CARD_TYPES = ["Visa", "Mastercard", "American Express", "Discover", "Diners Club International", "JCB", "UnionPay"]

CURRENCIES = ["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CHF", "CNY"]

ROLES = ["admin", "moderator", "user"]

def generate_random_date(min_age=18, max_age=80):
    """Generate a random birth date"""
    today = datetime.now()
    min_date = today - timedelta(days=max_age * 365)
    max_date = today - timedelta(days=min_age * 365)
    random_days = random.randint(0, (max_date - min_date).days)
    birth_date = min_date + timedelta(days=random_days)
    return birth_date.strftime("%Y-%m-%d")

def generate_address():
    """Generate a random address"""
    street_num = random.randint(100, 9999)
    street_names = ["Main Street", "Oak Street", "Maple Street", "First Street", "Second Street", "Third Street", "Fourth Street", "Fifth Street", "Sixth Street", "Washington Street", "Jefferson Street", "Lincoln Street", "Pine Street", "Cedar Street", "Elm Street"]
    street = random.choice(street_names)
    city = random.choice(CITIES)
    state = random.choice(STATES)
    postal_code = str(random.randint(10000, 99999))
    
    return {
        "address": f"{street_num} {street}",
        "city": city,
        "state": state,
        "stateCode": state[:2].upper(),
        "postalCode": postal_code,
        "coordinates": {
            "lat": round(random.uniform(-90, 90), 6),
            "lng": round(random.uniform(-180, 180), 6)
        },
        "country": "United States"
    }

def generate_bank():
    """Generate random bank information"""
    return {
        "cardExpire": f"{random.randint(1, 12):02d}/{random.randint(24, 35)}",
        "cardNumber": f"{random.randint(1000000000000000, 9999999999999999)}",
        "cardType": random.choice(CARD_TYPES),
        "currency": random.choice(CURRENCIES),
        "iban": f"{random.choice(['US', 'GB', 'DE', 'FR'])}{random.randint(10, 99)}{random.randint(1000000000000000000000000, 9999999999999999999999999)}"
    }

def generate_company():
    """Generate random company information"""
    company_names = ["Tech Corp", "Innovate Inc", "Global Solutions", "Digital Dynamics", "Future Systems", "Smart Technologies", "Data Driven", "Cloud First", "AI Solutions", "Next Gen"]
    
    return {
        "department": random.choice(DEPARTMENTS),
        "name": f"{random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones'])} - {random.choice(['Inc', 'LLC', 'Corp', 'Ltd'])}",
        "title": random.choice(TITLES),
        "address": generate_address()
    }

def generate_user_demographic(user_id):
    """Generate demographic data for a user"""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    username = f"{first_name.lower()}{last_name.lower()}{random.randint(1, 999)}"
    email = f"{first_name.lower()}.{last_name.lower()}@x.dummyjson.com"
    birth_date = generate_random_date()
    age = (datetime.now() - datetime.strptime(birth_date, "%Y-%m-%d")).days // 365
    
    return {
        "id": int(user_id),
        "firstName": first_name,
        "lastName": last_name,
        "maidenName": "",
        "age": age,
        "gender": random.choice(GENDERS),
        "email": email,
        "phone": f"+{random.randint(1, 999)} {random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
        "username": username,
        "password": f"{username}pass",
        "birthDate": birth_date,
        "image": f"https://dummyjson.com/icon/{username}/128",
        "bloodGroup": random.choice(BLOOD_GROUPS),
        "height": round(random.uniform(150.0, 200.0), 2),
        "weight": round(random.uniform(45.0, 120.0), 2),
        "eyeColor": random.choice(EYE_COLORS),
        "hair": {
            "color": random.choice(HAIR_COLORS),
            "type": random.choice(HAIR_TYPES)
        },
        "ip": f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
        "address": generate_address(),
        "macAddress": f"{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}",
        "university": random.choice(UNIVERSITIES),
        "bank": generate_bank(),
        "company": generate_company(),
        "ein": f"{random.randint(100, 999)}-{random.randint(100, 999)}",
        "ssn": f"{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(100, 999)}",
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36",
        "crypto": {
            "coin": "Bitcoin",
            "wallet": f"0x{''.join(random.choices('0123456789abcdef', k=40))}",
            "network": "Ethereum (ERC20)"
        },
        "role": random.choice(ROLES)
    }

def fetch_users():
    # Extract unique user IDs from events.csv and generate demographic data for them
    
    logger.info("Starting to extract user IDs from events.csv")
    
    unique_ids = set()
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    events_path = os.path.join(base_dir, 'data/raw/events.csv')
    
    try:
        with open(events_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                unique_ids.add(row['user_id'])
        
        logger.info(f"Found {len(unique_ids)} unique user IDs in events.csv")
    except FileNotFoundError:
        logger.error(f"Events file not found at {events_path}")
        return []
    except Exception as e:
        logger.error(f"Error reading events file: {str(e)}")
        return []
    
    logger.info("Generating demographic data for each user")
    
    all_users = []
    for i, user_id in enumerate(unique_ids):
        if i % 100000 == 0:
            logger.info(f"Processed {i}/{len(unique_ids)} users")
        
        user_data = generate_user_demographic(user_id)
        all_users.append(user_data)
    
    logger.info(f"Generated demographic data for {len(all_users)} users")
    
    # Save the combined result to a JSON file
    output_path = os.path.join(base_dir, 'data/raw/users.json')
    os.makedirs(os.path.join(base_dir, 'data/raw'), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(all_users, f, indent=2)
    
    logger.info(f"Saved {len(all_users)} users to {output_path}")
    
    return all_users

if __name__ == "__main__":
    fetch_users()
